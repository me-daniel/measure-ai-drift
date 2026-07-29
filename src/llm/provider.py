"""Config-driven LLM provider using OpenAI-compatible APIs.

All providers (Groq, Scaleway, OpenAI, Gemini, OpenRouter) use the same
OpenAI-compatible interface, simplifying the codebase to a single code path.

Usage:
    therapist_llm = create_provider("therapist")
    content, usage = await therapist_llm.generate([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ])
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import logging
import os

import yaml

import re

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "models.yaml"

# Regex patterns to strip Llama instruction tokens that leak through some APIs
_LLAMA_TOKEN_RE = re.compile(r"<\|[^>]+\|>")
_LLAMA_HEADER_RE = re.compile(r"<\|start_header_id\|>.*?<\|end_header_id\|>", re.DOTALL)


def _strip_llm_tokens(content: str) -> str:
    """Strip leaked instruction tokens from LLM output."""
    # First strip header blocks (e.g., <|start_header_id|>assistant<|end_header_id|>)
    content = _LLAMA_HEADER_RE.sub("", content)
    # Then strip any remaining tokens
    content = _LLAMA_TOKEN_RE.sub("", content)
    return content.strip()


@dataclass
class LLMConfig:
    """Configuration for an LLM provider instance."""
    provider: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 1024
    api_key: str = ""
    base_url: str = ""
    extra_params: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.provider:
            raise ValueError("Provider name is required")
        if not self.model:
            raise ValueError("Model name is required")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"Temperature must be 0.0-2.0, got {self.temperature}")
        if self.max_tokens < 1:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")


class LLMProvider:
    """Unified provider for OpenAI-compatible LLM backends."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._client = self._create_client()

    def _create_client(self) -> Any:
        try:
            from openai import AsyncOpenAI
        except ImportError as e:
            raise ImportError("Install openai: pip install openai") from e

        if not self.config.api_key:
            raise ValueError(
                f"API key required for provider '{self.config.provider}'. "
                f"Set the appropriate environment variable."
            )

        return AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url or None
        )

    async def generate(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any
    ) -> tuple[str, dict[str, Any]]:
        """Generate a completion from the model.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            **kwargs: Override temperature, max_tokens, or pass extra API params

        Returns:
            Tuple of (generated_content, usage_dict)
        """
        temperature = kwargs.pop("temperature", self.config.temperature)
        max_tokens = kwargs.pop("max_tokens", self.config.max_tokens)

        # Standard OpenAI params that can be passed directly
        standard_params = {
            "frequency_penalty", "logit_bias", "logprobs", "top_logprobs",
            "n", "presence_penalty", "response_format", "seed", "stop",
            "tools", "tool_choice", "user", "top_p",
        }

        all_params = {**self.config.extra_params, **kwargs}
        api_kwargs = {}
        extra_body = {}

        for key, value in all_params.items():
            if key in standard_params:
                api_kwargs[key] = value
            else:
                extra_body[key] = value

        if extra_body:
            api_kwargs["extra_body"] = extra_body

        # Native OpenAI rejects max_tokens for GPT-5.x; gateways translate it
        if self.config.provider == "openai":
            api_kwargs["max_completion_tokens"] = max_tokens
        else:
            api_kwargs["max_tokens"] = max_tokens

        response = await self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=temperature,
            **api_kwargs
        )

        content = response.choices[0].message.content or ""
        content = _strip_llm_tokens(content)
        usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
            "model": response.model,
            # OpenRouter reports which upstream provider served the request;
            # None for direct APIs. Persisted per trial via plan/response usage.
            "provider": getattr(response, "provider", None),
        }

        logger.debug(f"{self.config.provider}/{self.config.model}: {usage['total_tokens']} tokens")
        return content, usage

    def __repr__(self) -> str:
        return f"LLMProvider({self.config.provider}/{self.config.model})"


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load the models.yaml configuration."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        config = yaml.safe_load(f)

    for section in ["providers", "model_options", "roles"]:
        if section not in config:
            raise ValueError(f"Config missing required section: '{section}'")

    return config


def create_provider(
    role: str,
    config_path: str | Path | None = None,
    experiment: bool = False,
) -> LLMProvider:
    """Create provider for a role (therapist/patient/router/judge).

    Args:
        role: Role identifier from config, or evaluation model name
        config_path: Optional path to config file
        experiment: If True, use experiment-tier model for roles that define
            a ``use_experiment`` key (e.g. judge upgrades to gemini31_pro).

    Returns:
        Configured LLMProvider instance
    """
    config = load_config(config_path)
    model_options = config.get("model_options", {})

    # Look up role in roles section
    if role in config.get("roles", {}):
        role_config = config["roles"][role]
        use_key = role_config.get("use")
        # Upgrade to experiment tier when available and requested
        if experiment and "use_experiment" in role_config:
            use_key = role_config["use_experiment"]

        if use_key and role in model_options:
            model_def = model_options[role].get(use_key)
            if not model_def:
                available = list(model_options[role].keys())
                raise ValueError(f"Model '{use_key}' not found for '{role}'. Available: {available}")
            provider_name = model_def["provider"]
            model_name = model_def["model"]
        else:
            provider_name = role_config.get("provider", "")
            model_name = role_config.get("model", "")

    # Check evaluation_targets
    elif "evaluation_targets" in config:
        eval_model = next((m for m in config["evaluation_targets"] if m.get("name") == role), None)
        if eval_model:
            role_config = eval_model
            provider_name = eval_model["provider"]
            model_name = eval_model["model"]
        else:
            raise ValueError(f"Role '{role}' not found. Available: {list(config.get('roles', {}).keys())}")
    else:
        raise ValueError(f"Role '{role}' not found. Available: {list(config.get('roles', {}).keys())}")

    # Get provider details
    if provider_name not in config["providers"]:
        raise ValueError(f"Provider '{provider_name}' not found. Available: {list(config['providers'].keys())}")

    provider_config = config["providers"][provider_name]
    api_key_env = provider_config.get("api_key_env", "")
    api_key = os.environ.get(api_key_env, "")

    if not api_key:
        logger.warning(f"API key not found for '{provider_name}'. Set: {api_key_env}")

    llm_config = LLMConfig(
        provider=provider_name,
        model=model_name,
        temperature=role_config.get("temperature", 0.0),
        max_tokens=role_config.get("max_tokens", 1024),
        api_key=api_key,
        base_url=provider_config.get("base_url", ""),
        extra_params=role_config.get("extra_params", {}),
    )

    logger.info(f"Created provider for '{role}': {provider_name}/{model_name}")
    return LLMProvider(llm_config)
