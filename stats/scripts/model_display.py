"""Shared model display names, colors, and ordering for all figures."""

# Internal name -> display name for figures and tables
MODEL_NAMES = {
    # Mistral EU-sovereign
    "mistral_small32": "Mistral Small 3.2",
    "mistral_small4": "Mistral Small 4",
    "mistral_medium35": "Mistral Medium 3.5",
    "mistral_large": "Mistral Large 3",
    # Qwen family
    "qwen35_27b": "Qwen 3.5 27B",
    "qwen35_122b": "Qwen 3.5 122B",
    "qwen35_397b": "Qwen 3.5 397B",
    # Dense comparators
    "olmo3_32b": "OLMo 3.1 32B",
    "llama70b": "Llama 3.3 70B",
    # Proprietary
    "gpt54": "GPT-5.4",
    "sonnet46": "Claude Sonnet 4.6",
    # Test
    "llama70b_test": "Llama 70B (test)",
    "gpt_oss_test": "GPT-oss 120B (test)",
}

# Canonical display order for all figures and tables
MODEL_ORDER = [
    "mistral_small32",
    "mistral_small4",
    "mistral_medium35",
    "mistral_large",
    "qwen35_27b",
    "qwen35_122b",
    "qwen35_397b",
    "olmo3_32b",
    "llama70b",
    "gpt54",
    "sonnet46",
]

# Family panels for grouped figures (fig_jaccard, fig_bertscore)
MODEL_GROUPS = {
    "Mistral family": ["mistral_small32", "mistral_small4", "mistral_medium35", "mistral_large"],
    "Qwen family": ["qwen35_27b", "qwen35_122b", "qwen35_397b"],
    "US models": ["olmo3_32b", "llama70b", "gpt54", "sonnet46"],
}

MODEL_COLORS = {
    # Mistral EU-sovereign (orange, lighter=smaller, Small 4 slightly reddish)
    "mistral_small32": "#f4a261",    # light orange (24B, smallest)
    "mistral_small4": "#e76f51",     # reddish orange (119B, primary subject)
    "mistral_medium35": "#d65f43",   # mid orange-red (128B dense, post-hoc addition)
    "mistral_large": "#c44536",      # dark orange-red (675B, largest)
    # Qwen family (violet to purple, lighter=smaller)
    "qwen35_27b": "#b89dd6",        # light violet-pink (27B, smallest)
    "qwen35_122b": "#8e6bbf",       # medium purple (122B)
    "qwen35_397b": "#5a2d82",       # dark purple (397B, largest)
    # Dense comparators
    "olmo3_32b": "#e891b2",         # pink
    "llama70b": "#3a86c8",          # blue
    # Proprietary ceiling
    "sonnet46": "#8b5e3c",          # brown
    "gpt54": "#1a1a1a",             # black
    # Test
    "llama70b_test": "#a8c8e8",     # light blue
    "gpt_oss_test": "#6d6875",      # gray
}


def set_paper_style() -> None:
    """Font sizes tuned so figures stay legible after shrinking to text width.

    Multi-panel figures are ~13in wide and print at ~7in, so fonts must be
    roughly double the target print size.
    """
    import matplotlib as mpl
    mpl.rcParams.update({
        "font.size": 13,
        "axes.titlesize": 14,
        "axes.labelsize": 13,
        "xtick.labelsize": 11.5,
        "ytick.labelsize": 11.5,
        "legend.fontsize": 10.5,
        "figure.titlesize": 15,
    })


def display_name(internal_name: str) -> str:
    """Get display name for a model, fallback to internal name."""
    return MODEL_NAMES.get(internal_name, internal_name)


def sort_models(model_list: list[str]) -> list[str]:
    """Sort models by canonical display order. Unknown models go at the end."""
    order_map = {m: i for i, m in enumerate(MODEL_ORDER)}
    return sorted(model_list, key=lambda m: order_map.get(m, 999))
