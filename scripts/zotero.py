#!/usr/bin/env python3
"""Add and search sources in Zotero from the command line.

Primary path: Zotero desktop's local HTTP server (localhost:23119).
  add    -> POST /connector/saveItems (saves into the currently selected
            collection, exactly like the browser connector)
  search -> GET /api/users/0/items?q=... (needs "Allow other applications on
            this computer to communicate with Zotero" in Settings > Advanced)

Fallback for `add` when Zotero is not running: write a .ris file and open it,
which triggers the normal Zotero import dialog on next launch.

Examples:
  python3 scripts/zotero.py add --title "GLM 5.2 model card" \
      --url "https://huggingface.co/zai-org/GLM-5.2" --site "Hugging Face"
  python3 scripts/zotero.py add --json items.json
  python3 scripts/zotero.py search "sampling parameters"
"""

import argparse
import datetime
import json
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE = "http://localhost:23119"


def _request(url: str, data: dict | None = None) -> tuple[int, str]:
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, r.read().decode()


def build_item(args: argparse.Namespace) -> dict:
    item = {
        "itemType": args.type,
        "title": args.title,
        "url": args.url,
        "accessDate": args.accessed or datetime.date.today().isoformat(),
    }
    if args.site:
        item["websiteTitle"] = args.site
    if args.date:
        item["date"] = args.date
    if args.author:
        item["creators"] = [
            {"creatorType": "author", "name": a.strip()}
            for a in args.author.split(";")
        ]
    if args.publisher:
        field = "institution" if args.type == "report" else "publisher"
        item[field] = args.publisher
    for flag, field in (("place", "place"), ("language", "language"),
                        ("license", "rights"), ("short_title", "shortTitle"),
                        ("website_type", "websiteType"), ("doi", "DOI")):
        value = getattr(args, flag, None)
        if value:
            item[field] = value
    extra_lines = []
    if args.citekey:
        # Better BibTeX pins the citation key from this Extra line
        extra_lines.append(f"Citation Key: {args.citekey}")
    if args.extra:
        extra_lines.append(args.extra)
    if extra_lines:
        item["extra"] = "\n".join(extra_lines)
    return item


def ris_escape(items: list[dict]) -> str:
    type_map = {"webpage": "ELEC", "report": "RPRT", "preprint": "UNPB"}
    lines = []
    for it in items:
        lines.append(f"TY  - {type_map.get(it.get('itemType'), 'ELEC')}")
        lines.append(f"TI  - {it.get('title', '')}")
        for c in it.get("creators", []):
            lines.append(f"AU  - {c.get('name') or c.get('lastName', '')}")
        if it.get("url"):
            lines.append(f"UR  - {it['url']}")
        if it.get("date"):
            lines.append(f"PY  - {it['date']}")
        if it.get("accessDate"):
            lines.append(f"Y2  - {it['accessDate']}")
        if it.get("extra"):
            lines.append(f"N1  - {it['extra']}")
        lines.append("ER  - ")
    return "\n".join(lines) + "\n"


def cmd_add(args: argparse.Namespace) -> int:
    if args.json:
        with open(args.json) as f:
            items = json.load(f)
        if isinstance(items, dict):
            items = [items]
    else:
        if not (args.title and args.url):
            print("error: --title and --url required (or use --json)",
                  file=sys.stderr)
            return 2
        items = [build_item(args)]

    if args.dry_run:
        print(json.dumps(items, indent=2))
        return 0

    payload = {
        "items": items,
        "uri": items[0].get("url", "http://localhost/"),
        "sessionID": str(uuid.uuid4()),
    }
    try:
        status, _ = _request(f"{BASE}/connector/saveItems", payload)
        print(f"saved {len(items)} item(s) to Zotero "
              f"(currently selected collection), HTTP {status}")
        return 0
    except (urllib.error.URLError, OSError):
        pass

    # Zotero not running: write RIS and hand it to the OS
    ris = ris_escape(items)
    path = tempfile.mktemp(suffix=".ris", prefix="zotero_")
    with open(path, "w") as f:
        f.write(ris)
    print("Zotero desktop not reachable on localhost:23119.")
    print(f"Wrote RIS fallback: {path}")
    if not args.no_open:
        subprocess.run(["open", path], check=False)
        print("Opened it: Zotero will show its import dialog.")
    return 0


def _collections() -> dict[str, str]:
    """Collection key -> name for My Library."""
    _, body = _request(f"{BASE}/api/users/0/collections?format=json")
    return {c["key"]: c["data"]["name"] for c in json.loads(body)}


def _scopes(match: str | None) -> list[tuple[str, str]]:
    """[(items_url_prefix, display_name)] to search.

    Default: My Library + group libraries (covers everything once).
    With `match`: only groups/collections whose name contains it.
    """
    groups = []
    try:
        _, body = _request(f"{BASE}/api/users/0/groups?format=json")
        for g in json.loads(body):
            gid = g.get("id") or g.get("data", {}).get("id")
            name = g.get("data", {}).get("name") or g.get("name") or f"group {gid}"
            groups.append((f"{BASE}/api/groups/{gid}", name))
    except (urllib.error.URLError, OSError, ValueError):
        pass
    if not match:
        return [(f"{BASE}/api/users/0", "My Library")] + groups
    scopes = [(p, n) for p, n in groups if match.lower() in n.lower()]
    scopes += [
        (f"{BASE}/api/users/0/collections/{key}", name)
        for key, name in _collections().items()
        if match.lower() in name.lower()
    ]
    return scopes


def cmd_search(args: argparse.Namespace) -> int:
    q = urllib.parse.quote(args.query)
    try:
        scopes = _scopes(args.library)
        if not scopes:
            print(f"no library or collection matching {args.library!r}",
                  file=sys.stderr)
            return 1
        try:
            coll_names = _collections()
        except (urllib.error.URLError, OSError, ValueError):
            coll_names = {}
        found = 0
        for prefix, name in scopes:
            _, body = _request(
                f"{prefix}/items?q={q}&format=json&limit={args.limit}")
            for entry in json.loads(body):
                d = entry.get("data", {})
                found += 1
                colls = ", ".join(n for n in (coll_names.get(k, k)
                                  for k in d.get("collections", []))
                                  if n != name)
                where = f"{name} > {colls}" if colls else name
                print(f"[{where} / {entry.get('key')}] "
                      f"{d.get('itemType', '?'):<10} "
                      f"{d.get('title', '(no title)')}")
                if d.get("url"):
                    print(f"          {d['url']}")
        if not found:
            print("no matches")
        return 0
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:200]
        if e.code == 403:
            print("Zotero is running but its local API is off. Enable it in "
                  "Zotero Settings > Advanced > 'Enable local API', then "
                  "retry.", file=sys.stderr)
        else:
            print(f"Zotero local API error HTTP {e.code}: {detail}",
                  file=sys.stderr)
        return 1
    except (urllib.error.URLError, OSError):
        print("Zotero desktop not reachable on localhost:23119 - is it "
              "running?", file=sys.stderr)
        return 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="add source(s) to Zotero")
    a.add_argument("--title")
    a.add_argument("--url")
    a.add_argument("--type", default="webpage",
                   help="Zotero itemType (default: webpage)")
    a.add_argument("--site", help="websiteTitle, e.g. 'Hugging Face'")
    a.add_argument("--date", help="publication date, e.g. 2026-07-09")
    a.add_argument("--accessed", help="access date (default: today)")
    a.add_argument("--author", help="authors, ';'-separated (corporate ok, e.g. 'Z.ai')")
    a.add_argument("--publisher", help="publisher (institution for reports)")
    a.add_argument("--place", help="place of publication")
    a.add_argument("--language", help="e.g. en")
    a.add_argument("--license", help="rights field, e.g. 'MIT'")
    a.add_argument("--short-title", dest="short_title")
    a.add_argument("--website-type", dest="website_type",
                   help="e.g. 'Model card', 'Documentation'")
    a.add_argument("--doi")
    a.add_argument("--citekey",
                   help="pin Better BibTeX citation key, e.g. 'zai2026glm52'")
    a.add_argument("--extra", help="Zotero extra field")
    a.add_argument("--json", help="JSON file with an item or list of items")
    a.add_argument("--dry-run", action="store_true")
    a.add_argument("--no-open", action="store_true",
                   help="do not auto-open the RIS fallback")
    a.set_defaults(func=cmd_add)

    s = sub.add_parser("search",
                       help="search Zotero (My Library + all group libraries)")
    s.add_argument("query")
    s.add_argument("--library", help="restrict to library whose name contains this")
    s.add_argument("--limit", type=int, default=10)
    s.set_defaults(func=cmd_search)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
