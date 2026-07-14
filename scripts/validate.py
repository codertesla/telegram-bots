#!/usr/bin/env python3
"""
validate.py - Self-check script for bots data pipeline.

Per SPEC §4 Task D (M5):
- --check seed   : bots.json schema, required fields, id unique, category valid, featured <=5
- --check readme : markers paired, every non-dead json bot rendered in some marker block,
                   no stray/old bot links left inside marker blocks
- --check links  : every https://t.me/xxx inside marker blocks matches a bot's url in json
- --check dead   : every dead bot entry is rendered with "已失效" / ❗ marker
- (no arg)       : run ALL checks; exit 0 only if every check passes
"""

import argparse
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

VALID_CATEGORIES = {"search", "group", "download", "ai", "rss", "tools", "translate", "checkin", "channel", "game"}
VALID_SUBSECTIONS = {"verify", "ads", "stats", "misc", None, "bilingual", "auto", "zh-en", "publish", "index", "forward", "manage"}

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "bots.json"
README_FILE = ROOT / "README.md"


def load_bots():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_readme():
    with open(README_FILE, "r", encoding="utf-8") as f:
        return f.read()


def check_seed(data):
    """--check seed"""
    errors = []
    bots = data.get("bots", [])
    schema_version = data.get("schema_version")

    if schema_version != 1:
        errors.append(f"schema_version must be 1, got {schema_version}")

    ids = []
    featured_count = 0
    for i, bot in enumerate(bots):
        for field in ("id", "username", "url", "category", "featured", "official", "notes", "fetch"):
            if field not in bot:
                errors.append(f"bot[{i}] missing required field '{field}'")

        bid = bot.get("id")
        if not isinstance(bid, str) or not bid or " " in bid:
            errors.append(f"bot[{i}] id must be clean lowercase string without spaces, got {bid!r}")
        ids.append(bid)

        cat = bot.get("category")
        if cat not in VALID_CATEGORIES:
            errors.append(f"bot[{i}] ({bid}) invalid category '{cat}'")

        sub = bot.get("subsection")
        if sub not in VALID_SUBSECTIONS:
            errors.append(f"bot[{i}] ({bid}) invalid subsection '{sub}'")

        if not isinstance(bot.get("featured"), bool):
            errors.append(f"bot[{i}] ({bid}) 'featured' must be boolean")
        if bot.get("featured"):
            featured_count += 1

        if not isinstance(bot.get("official"), bool):
            errors.append(f"bot[{i}] ({bid}) 'official' must be boolean")

        fetch = bot.get("fetch")
        if not isinstance(fetch, dict) or "status" not in fetch:
            errors.append(f"bot[{i}] ({bid}) 'fetch' must be object with at least status")

    # unique ids
    seen = {}
    for bid in ids:
        if bid in seen:
            errors.append(f"duplicate id '{bid}'")
        seen[bid] = True

    if featured_count > 5:
        errors.append(f"featured count {featured_count} > 5 (SPEC limit)")

    if errors:
        print("SEED CHECK FAILED:")
        for e in errors:
            print(f"  - {e}")
        return False
    print(f"SEED CHECK PASSED: {len(bots)} bots, {featured_count} featured, schema v{schema_version}")
    return True


def extract_marker_inners(readme: str) -> dict:
    """Return dict of marker_name -> inner text between start/end (markers themselves excluded)."""
    inners = {}
    marker_names = [
        "last-verified",
        "bots-featured",
        "bots-category:search",
        "bots-category:group",
        "bots-category:download",
        "bots-category:ai",
        "bots-category:rss",
        "bots-category:tools",
        "bots-category:translate",
        "bots-category:checkin",
        "bots-category:channel",
        "bots-category:game",
    ]
    for m in marker_names:
        start = f"<!-- AUTO:{m}:start -->"
        end = f"<!-- AUTO:{m}:end -->"
        s = readme.find(start)
        e = readme.find(end, s + 1) if s >= 0 else -1
        if s >= 0 and e > s:
            inner = readme[s + len(start): e]
            inners[m] = inner
    return inners


def find_marker_pairs(readme: str):
    """Return list of (marker, has_pair) and overall ok."""
    errors = []
    marker_names = [
        "last-verified", "bots-featured",
        "bots-category:search", "bots-category:group", "bots-category:download",
        "bots-category:ai", "bots-category:rss", "bots-category:tools",
        "bots-category:translate", "bots-category:checkin", "bots-category:channel",
        "bots-category:game",
    ]
    for m in marker_names:
        start = f"<!-- AUTO:{m}:start -->"
        end = f"<!-- AUTO:{m}:end -->"
        sc = readme.count(start)
        ec = readme.count(end)
        if sc != 1 or ec != 1:
            errors.append(f"marker {m} not exactly one start+end pair (start={sc}, end={ec})")
        elif readme.find(start) > readme.find(end):
            errors.append(f"marker {m} end appears before start")
    return errors


def collect_rendered_urls(inners: dict) -> set:
    urls = set()
    for inner in inners.values():
        found = re.findall(r'https://t\.me/([A-Za-z0-9_]+)', inner)
        for u in found:
            urls.add(f"https://t.me/{u}")
    return urls


def check_readme(data, readme):
    """--check readme : pairs + coverage (non-dead must appear) + no residual old links"""
    errors = []

    # pairs
    pair_errs = find_marker_pairs(readme)
    errors.extend(pair_errs)

    inners = extract_marker_inners(readme)
    rendered_urls = collect_rendered_urls(inners)

    # non-dead bots must be present in rendered
    non_dead_urls = set()
    all_bot_urls = set()
    dead_urls = set()
    for b in data.get("bots", []):
        u = b.get("url")
        if u:
            all_bot_urls.add(u)
        if b.get("fetch", {}).get("status") == "dead":
            if u:
                dead_urls.add(u)
        else:
            if u:
                non_dead_urls.add(u)

    missing = non_dead_urls - rendered_urls
    if missing:
        errors.append(f"non-dead bots missing from rendered marker blocks: {sorted(missing)}")

    # stray / old urls inside markers that are not in current json at all
    stray = rendered_urls - all_bot_urls
    if stray:
        errors.append(f"stray/old bot links inside marker blocks not in json: {sorted(stray)}")

    if errors:
        print("README CHECK FAILED:")
        for e in errors:
            print(f"  - {e}")
        return False
    print(f"README CHECK PASSED: {len(non_dead_urls)} non-dead bots covered in markers, no stray links")
    return True


def check_links(data, readme):
    """--check links : marker-block urls must exactly correspond to json urls (consistency)"""
    errors = []
    inners = extract_marker_inners(readme)
    rendered_urls = collect_rendered_urls(inners)

    url_to_bot = {}
    for b in data.get("bots", []):
        u = b.get("url")
        if u:
            url_to_bot[u] = b["id"]

    for u in sorted(rendered_urls):
        if u not in url_to_bot:
            errors.append(f"rendered url has no matching bot in json: {u}")

    # Also ensure every json url that should render appears (covered by readme check too)
    # But for links we focus on "all rendered == known"
    if errors:
        print("LINKS CHECK FAILED:")
        for e in errors:
            print(f"  - {e}")
        return False
    print(f"LINKS CHECK PASSED: {len(rendered_urls)} t.me links in markers all match json bots")
    return True


def check_dead(data, readme):
    """--check dead : dead bots must carry failure marker in their rendered line"""
    errors = []
    inners = extract_marker_inners(readme)
    combined = "\n".join(inners.values())

    dead_bots = [b for b in data.get("bots", []) if b.get("fetch", {}).get("status") == "dead"]

    for b in dead_bots:
        bid = b["id"]
        u = b.get("username", "").lstrip("@")
        url = b.get("url", "")
        # Must appear and contain failure indicator near it
        # Look for the url or username + 已失效 / ❗
        if url and url in combined:
            # find surrounding context
            idx = combined.find(url)
            window = combined[max(0, idx-30): idx+120]
            if "已失效" not in window and "❗" not in window:
                errors.append(f"dead bot {bid} rendered but missing '已失效' / ❗ marker")
        else:
            # not even the link? still fail (though readme check may catch for non-dead, dead are optional in readme spec but we render them)
            errors.append(f"dead bot {bid} link not found in any marker block (should still be shown with failure note)")

    if errors:
        print("DEAD CHECK FAILED:")
        for e in errors:
            print(f"  - {e}")
        return False
    print(f"DEAD CHECK PASSED: {len(dead_bots)} dead bot(s) correctly marked")
    return True


def main():
    parser = argparse.ArgumentParser(description="Validate bots data and pipeline state (M4/M5)")
    parser.add_argument("--check", choices=["seed", "readme", "links", "dead"], help="Run specific check (default = all)")
    args = parser.parse_args()

    try:
        data = load_bots()
    except Exception as e:
        print(f"Failed to load {DATA_FILE}: {e}")
        sys.exit(2)

    try:
        readme = load_readme()
    except Exception as e:
        print(f"Failed to load {README_FILE}: {e}")
        sys.exit(2)

    ok = True

    checks_to_run = []
    if args.check is None:
        checks_to_run = ["seed", "readme", "links", "dead"]
    else:
        checks_to_run = [args.check]

    for chk in checks_to_run:
        if chk == "seed":
            ok = check_seed(data) and ok
        elif chk == "readme":
            ok = check_readme(data, readme) and ok
        elif chk == "links":
            ok = check_links(data, readme) and ok
        elif chk == "dead":
            ok = check_dead(data, readme) and ok

    if args.check is None:
        if ok:
            print("FULL VALIDATION PASSED (all checks).")
        else:
            print("FULL VALIDATION FAILED (see above).")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
