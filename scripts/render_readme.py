#!/usr/bin/env python3
"""
render_readme.py - Render bots data into README.md marker blocks.

Per SPEC §4 Task C (M4):
- Reads data/bots.json (sole source of truth for bot list content)
- Replaces ONLY content inside AUTO:* markers
- Leaves all prose, headings, and non-marker text byte-for-byte unchanged
- Supports last-verified, bots-featured, and 6 category markers (search/group/download/ai/tools)
- Group category renders subsection headers (verify/ads/stats/misc)
- Dead bots are shown with failure marker; once fetch.dead_streak >= HIDE_AFTER
  (3 consecutive dead checks) they are hidden from README (kept in bots.json)
- Live pages that are not bots (fetch.not_bot) get a ⚠️ marker in the 月活 cell
- AI bots with url=null render as prose line only (no link)
"""

import json
from collections import defaultdict
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "bots.json"
README_FILE = ROOT / "README.md"

VALID_CATEGORIES = {"official", "search", "group", "download", "ai", "tools", "translate", "checkin", "channel", "game", "crypto"}

HIDE_AFTER = 3  # keep in sync with scripts/fetch_bots.py

NOT_BOT_LABELS = {
    "channel": "⚠️已变为频道（非 Bot）",
    "group": "⚠️已变为群组（非 Bot）",
    "user": "⚠️个人账号（非 Bot）",
}


def is_hidden(bot: dict) -> bool:
    """Dead for HIDE_AFTER consecutive checks -> hidden from README/site."""
    fetch = bot.get("fetch", {}) or {}
    return fetch.get("status") == "dead" and int(fetch.get("dead_streak") or 0) >= HIDE_AFTER


def sort_by_monthly(bots: list[dict]) -> list[dict]:
    """稳定排序：月活降序，无月活靠后，已失效最后。

    分类表与精选表都走这一条规则，保证每周自动刷新后顺序无需人工维护。
    同档内保持 bots.json 的原有相对次序。
    """
    def key(item):
        idx, bot = item
        fetch = bot.get("fetch", {}) or {}
        mu = fetch.get("monthly_users")
        if fetch.get("status") == "dead":
            return (2, 0, idx)
        if not mu or int(mu) < 10000:
            return (1, 0, idx)
        return (0, -int(mu), idx)

    return [bot for _, bot in sorted(enumerate(bots), key=key)]


def not_bot_label(bot: dict) -> str:
    fetch = bot.get("fetch", {}) or {}
    if fetch.get("status") == "ok" and fetch.get("not_bot"):
        return NOT_BOT_LABELS.get(fetch.get("page_kind"), "⚠️非 Bot")
    return ""


SUBSECTION_TITLES = {
    "verify": "**进群验证**",
    "ads": "**广告拦截**",
    "stats": "**活跃统计**",
    "misc": "**秩序维护**",
}


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def format_num(n: int) -> str:
    """Format monthly number per SPEC: >=1e4 use 万, >=1e8 use 亿. 1 decimal."""
    if n >= 100_000_000:
        return f"{n / 100_000_000:.1f} 亿"
    return f"{n / 10_000:.1f} 万"


def clean_display_title(raw: str) -> str:
    """Strip decorative emojis and redundant trailing @handles from bot display title."""
    import re
    s = re.sub(r"[🔍🤖🐴🇺🇦⚡️🎲🐰\ufe0f]+", "", raw)
    s = re.sub(r"\s*Powered by @[A-Za-z0-9_]+", "", s, flags=re.I)
    s = re.sub(r"\s*@[A-Za-z0-9_]+\s*$", "", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s


def get_display_name(bot: dict) -> str:
    fetch = bot.get("fetch", {}) or {}
    title = fetch.get("title")
    if title:
        cleaned = clean_display_title(str(title))
        if cleaned:
            return cleaned
    # fallback
    uname = bot.get("username", "") or bot.get("id", "")
    return uname.lstrip("@").strip() or bot.get("id", "")


def get_verified_suffix(bot: dict) -> str:
    fetch = bot.get("fetch", {}) or {}
    is_v = bool(fetch.get("is_verified"))
    official = bool(bot.get("official"))
    if (is_v or official) and fetch.get("status") != "dead":
        return " ✓"
    return ""


def get_monthly_cell(bot: dict) -> str:
    """For featured table 月活 column."""
    fetch = bot.get("fetch", {}) or {}
    status = fetch.get("status")
    if status == "dead":
        return "❌ 已失效"
    nb = not_bot_label(bot)
    mu = fetch.get("monthly_users")
    if nb and (not mu or mu < 10000):
        return nb
    if not mu or mu < 10000:
        return "—"
    num_str = format_num(int(mu))
    typ = (fetch.get("type") or "bot").lower()
    if typ == "channel":
        cell = f"{num_str} 订阅"
    elif typ == "group":
        cell = f"{num_str} 成员"
    else:
        cell = f"约 {num_str}/月"
    return f"{nb} · {cell}" if nb else cell


def get_active_badge(bot: dict) -> str:
    """For category list rows (kept for AI prose fallback only)."""
    fetch = bot.get("fetch", {}) or {}
    status = fetch.get("status")
    if status == "dead":
        fa = fetch.get("fetched_at") or ""
        mon = fa[:7] if fa and len(fa) >= 7 else ""
        if mon:
            return f" · ❗已失效（{mon}）"
        return " · ❗已失效"
    nb = not_bot_label(bot)
    if nb:
        return f" · {nb}"
    mu = fetch.get("monthly_users")
    if status != "ok" or not mu or mu < 10000:
        return ""
    num_str = format_num(int(mu))
    typ = (fetch.get("type") or "bot").lower()
    if typ == "channel":
        return f"（{num_str} 订阅）"
    elif typ == "group":
        return f"（{num_str} 成员）"
    else:
        return f"（约 {num_str}/月）"


def get_category_monthly(bot: dict) -> str:
    """Monthly label for category tables (per user spec).
    - dead: ❗已失效（YYYY-MM）
    - bot + >=10k: 约 X.X 万/月   (or 亿)
    - channel + >=10k: X.X 万 订阅
    - group + >=10k: X.X 万 成员
    - else: —
    """
    fetch = bot.get("fetch", {}) or {}
    status = fetch.get("status")
    if status == "dead":
        fa = fetch.get("fetched_at") or ""
        mon = fa[:7] if fa and len(fa) >= 7 else ""
        if mon:
            return f"❗已失效（{mon}）"
        return "❗已失效"
    nb = not_bot_label(bot)
    mu = fetch.get("monthly_users")
    if nb and (not mu or int(mu) < 10000):
        return nb
    if not mu or int(mu) < 10000:
        return "—"
    num_str = format_num(int(mu))
    typ = (fetch.get("type") or "bot").lower()
    if typ == "channel":
        cell = f"{num_str} 订阅"
    elif typ == "group":
        cell = f"{num_str} 成员"
    else:
        cell = f"约 {num_str}/月"
    return f"{nb} · {cell}" if nb else cell


def render_category_table_row(bot: dict) -> str:
    """Render a single | row | for category markdown tables. Escapes | ."""
    disp = get_display_name(bot) + get_verified_suffix(bot)
    uwo = bot.get("username", "").lstrip("@")
    url = bot.get("url")
    link = f"[@{uwo}]({url})" if uwo and url else ""
    purpose = (bot.get("notes") or "").strip()
    monthly = get_category_monthly(bot)
    # escape pipe chars inside cells (rare)
    disp = disp.replace("|", "｜")
    purpose = purpose.replace("|", "｜")
    link = link.replace("|", "｜")
    return f"| {disp} | {link} | {purpose} | {monthly} |"


def get_last_verified_label(data: dict) -> str:
    label = data.get("last_verified_label") or ""
    if label:
        return str(label).strip()
    lfa = data.get("last_fetched_at") or ""
    if lfa and len(lfa) >= 7:
        return lfa[:7]
    return "未知"


def render_list_item(bot: dict) -> str:
    """Render one - **name** [@u](url) — notes + badge line."""
    if not bot.get("url"):
        # AI placeholder url=null : render prose line only (no link)
        notes = bot.get("notes", "").strip()
        return notes or ""
    disp = get_display_name(bot) + get_verified_suffix(bot)
    uwo = bot.get("username", "").lstrip("@")
    url = bot.get("url")
    link = f"[@{uwo}]({url})" if uwo and url else ""
    notes = bot.get("notes", "").strip()
    badge = get_active_badge(bot)
    if link:
        if badge:
            return f"- **{disp}** {link} — {notes}{badge}"
        return f"- **{disp}** {link} — {notes}"
    # fallback
    return f"- **{disp}** — {notes}{badge}"


def render_featured_table(featured_bots: list[dict]) -> str:
    if not featured_bots:
        return ""
    lines = []
    lines.append("| 名称 | 链接 | 一句话用途 | 月活 |")
    lines.append("|------|------|------------|------|")
    for bot in featured_bots:
        disp = get_display_name(bot) + get_verified_suffix(bot)
        uwo = bot.get("username", "").lstrip("@")
        url = bot.get("url")
        link = f"[@{uwo}]({url})" if uwo and url else ""
        purpose = (bot.get("notes") or "").strip()
        monthly = get_monthly_cell(bot)
        # Basic escape for | inside text (rare)
        disp = disp.replace("|", "｜")
        purpose = purpose.replace("|", "｜")
        lines.append(f"| {disp} | {link} | {purpose} | {monthly} |")
    return "\n".join(lines)


def render_category(cat: str, bots_in_cat: list[dict]) -> str:
    """Render a category block as markdown table(s).
    - Most categories: single 4-col table (名称 | 链接 | 核心功能 | 月活)
    - group: 4 subsection titles, each followed by its own small table
    - ai: keep prose line rendering (url=null placeholders never go into table)
    Dead bots are included (月活 cell carries the ❗ marker).
    行序统一按月活降序（见 sort_by_monthly）。
    """
    if not bots_in_cat:
        return ""

    # AI category: never table the url=null prose placeholders. Use legacy prose render.
    if cat == "ai":
        lines = []
        for b in sort_by_monthly(bots_in_cat):
            item = render_list_item(b)
            if item:
                lines.append(item)
        return "\n".join(lines)

    # Collect table-eligible (have url) vs prose-only
    table_bots = sort_by_monthly([b for b in bots_in_cat if b.get("url")])
    prose_only = [b for b in bots_in_cat if not b.get("url")]

    if cat == "group":
        by_sub: dict[str, list[dict]] = defaultdict(list)
        for b in table_bots:
            sub = b.get("subsection") or "misc"
            by_sub[sub].append(b)
        lines: list[str] = []
        order = ["verify", "ads", "stats", "misc"]
        for idx, sub in enumerate(order):
            items = by_sub.get(sub, [])
            if not items:
                continue
            if idx > 0:
                lines.append("")  # blank line before next subsection title
            title = SUBSECTION_TITLES.get(sub, f"**{sub}**")
            lines.append(title)
            lines.append("")  # blank before table header (visual + md)
            lines.append("| 名称 | 链接 | 核心功能 | 月活 |")
            lines.append("|------|------|----------|------|")
            for b in items:
                row = render_category_table_row(b)
                if row:
                    lines.append(row)
        # Any stray prose for group (should not happen) appended at end
        if prose_only:
            if lines:
                lines.append("")
            for b in prose_only:
                item = render_list_item(b)
                if item:
                    lines.append(item)
        return "\n".join(lines)

    # Normal categories (search, download, tools, translate, checkin, channel, game, ...)
    lines: list[str] = []
    if table_bots:
        lines.append("| 名称 | 链接 | 核心功能 | 月活 |")
        lines.append("|------|------|----------|------|")
        for b in table_bots:
            row = render_category_table_row(b)
            if row:
                lines.append(row)
    # Fallback: if no table bots but prose (e.g. future ai-like), keep prose
    if prose_only and not table_bots:
        for b in prose_only:
            item = render_list_item(b)
            if item:
                lines.append(item)
    return "\n".join(lines)


def replace_marker_block(text: str, marker: str, replacement: str) -> str:
    """Replace inner content between <!-- AUTO:xxx:start --> and :end -->.

    Preserves the marker lines themselves. Works line-based for safety.
    """
    start_tag = f"<!-- AUTO:{marker}:start -->"
    end_tag = f"<!-- AUTO:{marker}:end -->"

    lines = text.splitlines(keepends=True)

    start_idx = None
    end_idx = None
    for i, ln in enumerate(lines):
        if start_tag in ln:
            start_idx = i
        if end_tag in ln and start_idx is not None:
            end_idx = i
            break

    if start_idx is None or end_idx is None or end_idx <= start_idx:
        raise RuntimeError(f"Marker pair not found or invalid for {marker}")

    # Build replacement block: keep start line, insert replacement (normalized), keep end line
    start_line = lines[start_idx]
    end_line = lines[end_idx]

    # Normalize replacement to lines with proper endings
    if replacement:
        repl_lines = []
        for rline in replacement.splitlines():
            if rline.endswith("\n"):
                repl_lines.append(rline)
            else:
                repl_lines.append(rline + "\n")
        # If replacement ends without trailing blank intent, ok
    else:
        repl_lines = []

    new_lines = lines[: start_idx + 1] + repl_lines + lines[end_idx:]
    return "".join(new_lines)


def main():
    data = load_data()
    all_bots = data.get("bots", [])
    if not all_bots:
        print("No bots in data/bots.json")
        return
    hidden = [b for b in all_bots if is_hidden(b)]
    bots = [b for b in all_bots if not is_hidden(b)]

    # Group by category. 行序不再依赖 json 顺序：分类表与精选表都在渲染时
    # 按月活降序排序（sort_by_monthly），每周自动刷新后无需人工重排。
    # 精选条目同时在所属分类里出现一次，避免只看分类表时漏掉头部入口。
    featured = sort_by_monthly([b for b in bots if b.get("featured")])

    by_cat: dict[str, list[dict]] = defaultdict(list)
    for b in bots:
        cat = b.get("category")
        if cat in VALID_CATEGORIES:
            by_cat[cat].append(b)

    readme = README_FILE.read_text(encoding="utf-8")

    # 1. last-verified
    last_label = get_last_verified_label(data)
    last_block = f"> 最近核验：{last_label}"
    readme = replace_marker_block(readme, "last-verified", last_block)

    # 2. featured table
    feat_block = render_featured_table(featured)
    readme = replace_marker_block(readme, "bots-featured", feat_block)

    # 3. categories
    cat_markers = {
        "official": "bots-category:official",
        "search": "bots-category:search",
        "group": "bots-category:group",
        "download": "bots-category:download",
        "ai": "bots-category:ai",
        "tools": "bots-category:tools",
        "translate": "bots-category:translate",
        "checkin": "bots-category:checkin",
        "channel": "bots-category:channel",
        "game": "bots-category:game",
        "crypto": "bots-category:crypto",
    }
    for cat, marker in cat_markers.items():
        cat_bots = by_cat.get(cat, [])
        block = render_category(cat, cat_bots)
        readme = replace_marker_block(readme, marker, block)

    # Write back
    README_FILE.write_text(readme, encoding="utf-8")
    print(f"README.md rendered successfully.")
    print(f"  - last-verified: {last_label}")
    print(f"  - featured: {len(featured)} entries")
    if hidden:
        print(f"  - hidden (dead x{HIDE_AFTER}+): {', '.join(b['id'] for b in hidden)}")
    for cat in ["official", "search", "group", "download", "ai", "tools", "translate", "checkin", "channel", "game", "crypto"]:
        print(f"  - {cat}: {len(by_cat.get(cat, []))} entries")


if __name__ == "__main__":
    main()
