#!/usr/bin/env python3
"""
validate.py - Self-check script for bots data pipeline.

Per SPEC §4 Task D (M5):
- --check seed   : bots.json schema, required fields, id unique, category valid, featured <=5
- --check readme : markers paired, every non-dead json bot rendered in some marker block,
                   no stray/old bot links left inside marker blocks
- --check links  : every https://t.me/xxx inside marker blocks matches a bot's url in json
- --check order  : each category block is sorted by monthly users desc (no-data last,
                   dead last); guards the auto-sorting rule in the renderers
- --check dead   : every visible dead bot entry is rendered with "已失效" / ❗ marker;
                   entries dead for HIDE_AFTER consecutive checks must NOT be rendered
- --check notbot : live pages that are not bots (fetch.not_bot) carry a ⚠️ marker;
                   prints a warning listing them so maintainers can review/remove
- --check provenance : fetch 字段必须可由抓取脚本复现（extra_raw ↔ monthly_users、
                   http_code、时间戳指纹、顶层批次时间）；拦截手工编造的月活数据
- (no arg)       : run ALL checks; exit 0 only if every check passes
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import Counter, defaultdict

VALID_CATEGORIES = {"official", "search", "group", "download", "ai", "tools", "translate", "checkin", "channel", "game", "crypto"}
VALID_SUBSECTIONS = {"verify", "ads", "stats", "misc", None, "bilingual", "auto", "zh-en", "publish", "index", "forward", "manage"}

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "bots.json"
README_FILE = ROOT / "README.md"
HIDE_AFTER = 3  # keep in sync with scripts/fetch_bots.py


def is_hidden(bot) -> bool:
    fetch = bot.get("fetch", {}) or {}
    return fetch.get("status") == "dead" and int(fetch.get("dead_streak") or 0) >= HIDE_AFTER


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
        else:
            ds = fetch.get("dead_streak", 0)
            if ds is not None and (not isinstance(ds, int) or ds < 0):
                errors.append(f"bot[{i}] ({bid}) fetch.dead_streak must be a non-negative int, got {ds!r}")
            if fetch.get("status") not in ("ok", "dead", "error", "pending"):
                errors.append(f"bot[{i}] ({bid}) invalid fetch.status {fetch.get('status')!r}")

    # unique ids
    seen = {}
    for bid in ids:
        if bid in seen:
            errors.append(f"duplicate id '{bid}'")
        seen[bid] = True

    if featured_count > 5:
        errors.append(f"featured count {featured_count} > 5 (SPEC limit)")

    # 顶层 featured_order 是精选区的人工顺序；一旦声明，必须与 featured=true
    # 的集合完全一致，避免增删精选后顺序表静默失配（缺失时退回月活降序）。
    fo = data.get("featured_order")
    if fo is not None:
        if not isinstance(fo, list) or not all(
            isinstance(u, str) and u.strip() for u in fo
        ):
            errors.append("featured_order must be a list of non-empty username strings")
        else:
            norm = [u.lower().lstrip("@") for u in fo]
            if len(set(norm)) != len(norm):
                errors.append("featured_order contains duplicate usernames")
            featured_set = {
                str(b.get("username", "")).lower().lstrip("@")
                for b in bots
                if b.get("featured")
            }
            missing = featured_set - set(norm)
            extra = set(norm) - featured_set
            if missing or extra:
                errors.append(
                    "featured_order must list exactly the featured bots "
                    f"(missing: {sorted(missing)}, not featured: {sorted(extra)})"
                )

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
        "bots-category:official",
        "bots-category:search",
        "bots-category:group",
        "bots-category:download",
        "bots-category:ai",
        "bots-category:tools",
        "bots-category:translate",
        "bots-category:checkin",
        "bots-category:channel",
        "bots-category:game",
        "bots-category:crypto",
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
        "bots-category:official", "bots-category:search", "bots-category:group", "bots-category:download",
        "bots-category:ai", "bots-category:tools",
        "bots-category:translate", "bots-category:checkin", "bots-category:channel",
        "bots-category:game", "bots-category:crypto",
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
        # Keep an optional ?start=... deep-link suffix so urls match json exactly
        found = re.findall(r'https://t\.me/[A-Za-z0-9_]+(?:\?[A-Za-z0-9_=&%.:+-]*)?', inner)
        for u in found:
            urls.add(u.rstrip(".,;"))
    return urls


def check_readme(data, readme):
    """--check readme : pairs + coverage (non-dead must appear) + no residual old links"""
    errors = []

    # pairs
    pair_errs = find_marker_pairs(readme)
    errors.extend(pair_errs)

    inners = extract_marker_inners(readme)
    rendered_urls = collect_rendered_urls(inners)

    # visible (non-hidden) bots must be present in rendered; hidden ones must not
    non_dead_urls = set()
    visible_urls = set()
    hidden_urls = set()
    for b in data.get("bots", []):
        u = b.get("url")
        if not u:
            continue
        if is_hidden(b):
            hidden_urls.add(u)
            continue
        visible_urls.add(u)
        if b.get("fetch", {}).get("status") != "dead":
            non_dead_urls.add(u)

    missing = visible_urls - rendered_urls
    if missing:
        errors.append(f"visible bots missing from rendered marker blocks: {sorted(missing)}")

    leaked = hidden_urls & rendered_urls
    if leaked:
        errors.append(f"hidden bots (dead x{HIDE_AFTER}+) still rendered: {sorted(leaked)}")

    # stray / old urls inside markers that are not visible json bots
    stray = rendered_urls - visible_urls - hidden_urls
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


def rank_key(bot):
    """与 render_readme.sort_by_monthly 一致的排序键（越靠前越小）。"""
    fetch = bot.get("fetch", {}) or {}
    mu = fetch.get("monthly_users")
    if fetch.get("status") == "dead":
        return (2, 0)
    if not mu or int(mu) < 10000:
        return (1, 0)
    return (0, -int(mu))


def check_order(data, readme):
    """--check order : 每个分类块内必须排列为 月活降序 / 无数据置底 / 失效最后。

    渲染器已内置排序，本检查防回归：手改 README 表格或改坏排序逻辑都会被抓住。
    """
    errors = []
    inners = extract_marker_inners(readme)
    url_to_bot = {b["url"]: b for b in data.get("bots", []) if b.get("url")}

    for marker, inner in sorted(inners.items()):
        if not marker.startswith("bots-category:"):
            continue
        prev = None
        for line in inner.splitlines():
            m = re.search(r'https://t\.me/[A-Za-z0-9_]+(?:\?[A-Za-z0-9_=&%.:+-]*)?', line)
            if not m:
                # 群管类的小标题：各子表独立排序，遇到即重置比较基准
                if line.strip().startswith("**"):
                    prev = None
                continue
            bot = url_to_bot.get(m.group(0))
            if not bot:
                continue
            if prev is not None and rank_key(prev) > rank_key(bot):
                errors.append(f"{marker}: {bot['id']} 应排在 {prev['id']} 之前（月活降序被打乱）")
            prev = bot

    if errors:
        print("ORDER CHECK FAILED:")
        for e in errors:
            print(f"  - {e}")
        print("  hint: 运行 python scripts/render_readme.py 重新排序")
        return False
    print("ORDER CHECK PASSED: 各分类块均为 月活降序 / 无数据置底 / 失效最后")
    return True


def check_dead(data, readme):
    """--check dead : dead bots must carry failure marker in their rendered line"""
    errors = []
    inners = extract_marker_inners(readme)
    combined = "\n".join(inners.values())

    dead_bots = [b for b in data.get("bots", [])
                 if b.get("fetch", {}).get("status") == "dead" and not is_hidden(b)]

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


def check_notbot(data, readme):
    """--check notbot : not_bot entries must carry the ⚠️ marker; list them as a warning"""
    errors = []
    inners = extract_marker_inners(readme)
    combined = "\n".join(inners.values())
    flagged = [b for b in data.get("bots", [])
               if (b.get("fetch") or {}).get("status") == "ok" and (b.get("fetch") or {}).get("not_bot")
               and not is_hidden(b)]
    for b in flagged:
        url = b.get("url", "")
        line = next((ln for ln in combined.splitlines() if url and f"({url})" in ln), None)
        if line is None or "⚠️" not in line:
            errors.append(f"not_bot entry {b['id']} rendered without ⚠️ marker")
    if errors:
        print("NOTBOT CHECK FAILED:")
        for e in errors:
            print(f"  - {e}")
        return False
    # official 分类里的频道（@premium / @TAndroidAPK / @tgx_log）是刻意收录，
    # 且已在 README / 站点单独分组标注，不必按「疑似伪装 Bot」逐周告警。
    warned = [b for b in flagged if b.get("category") != "official"]
    if warned:
        kinds = ", ".join(f"{b['id']}({b['fetch'].get('page_kind')})" for b in warned)
        print(f"WARNING: {len(warned)} entr(y/ies) no longer look like bots, review/remove: {kinds}")
        if __import__("os").environ.get("GITHUB_ACTIONS"):
            print(f"::warning title=not_bot entries::{kinds}")
    print(f"NOTBOT CHECK PASSED: {len(flagged)} not_bot entr(y/ies) marked"
          f" ({len(flagged) - len(warned)} 官方频道已在渲染层单独分组)")
    return True


EXTRA_RAW_RE = re.compile(r"^\s*([\d\s\u00a0,\.]+?)\s+(monthly users|subscribers|members)\s*$", re.I)
CLOCK_SKEW = timedelta(minutes=5)


def parse_extra_raw(raw):
    """把 tgme_page_extra 原文反解成整数；无法识别返回 None。"""
    if not isinstance(raw, str):
        return None
    m = EXTRA_RAW_RE.match(raw)
    if not m:
        return None
    digits = re.sub(r"[\s\u00a0,\.]", "", m.group(1))
    return int(digits) if digits.isdigit() else None


def parse_fetched_at(raw):
    """解析脚本写入的 UTC ISO 时间戳；缺失/无时区/格式错误返回 None。"""
    if not isinstance(raw, str) or not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt.astimezone(timezone.utc)


def check_provenance(data, now=None):
    """--check provenance : fetch 字段必须具备「抓取脚本生成」的特征。

    背景：PR #8 把 12 条估算月活连同 extra_raw、http_code 一起手工写进 fetch，
    旧的六项检查全部放行。本检查从三面设防：
      1. monthly_users 必须能由 extra_raw 反解（双向一致），且 status=ok / http_code=200
      2. 抓取脚本每条间隔 ≥1s，写入的 fetched_at 取自各次请求的
         datetime.now().isoformat()，因此 ok 条目不得共享同一 fetched_at，也不得
         出现「整分零微秒」这类人工填写指纹（幂等保留的旧时间戳不受影响）
      3. fetched_at / last_fetched_at 不得为未来时间；条目时间不得晚于批次时间；
         last_fetched_at 不得与任何条目时间完全相同

    边界：这只能证明「数据具备脚本生成的特征」，不能替代真实抓取，也无法排除
    精心伪造的逐条时间戳。需要复核时请跑 `python scripts/fetch_bots.py --sleep 2`。
    """
    errors = []
    now = now or datetime.now(timezone.utc)
    bots = data.get("bots", [])

    top_raw = data.get("last_fetched_at")
    top_dt = parse_fetched_at(top_raw)
    if top_dt is None:
        errors.append(f"last_fetched_at 缺失或不是带时区的 ISO 时间: {top_raw!r}")
    else:
        if top_dt > now + CLOCK_SKEW:
            errors.append(f"last_fetched_at 在未来: {top_raw}")
        label = data.get("last_verified_label")
        if label and top_dt.strftime("%Y-%m") != label:
            errors.append(f"last_verified_label={label!r} 与 last_fetched_at={top_raw[:7]} 不一致")

    seen_times = Counter()
    for b in bots:
        bid = b.get("id") or b.get("username")
        f = b.get("fetch") or {}
        mu = f.get("monthly_users")
        raw = f.get("extra_raw")
        status = f.get("status")

        parsed = parse_extra_raw(raw)
        if mu is not None:
            if not isinstance(mu, int) or isinstance(mu, bool) or mu < 0:
                errors.append(f"{bid}: monthly_users 必须是非负整数, got {mu!r}")
            elif parsed is None:
                errors.append(f"{bid}: monthly_users={mu} 但 extra_raw 缺失或无法反解: {raw!r}")
            elif parsed != mu:
                errors.append(f"{bid}: extra_raw 反解为 {parsed}，与 monthly_users={mu} 不符")
            if status != "ok":
                errors.append(f"{bid}: 有月活数据但 status={status!r}（应为 ok）")
            if f.get("http_code") != 200:
                errors.append(f"{bid}: 有月活数据但 http_code={f.get('http_code')!r}（应为 200）")
        elif raw:
            errors.append(f"{bid}: extra_raw 有值但 monthly_users 为空: {raw!r}")

        fa_raw = f.get("fetched_at")
        fa_dt = parse_fetched_at(fa_raw)
        if fa_dt is None:
            errors.append(f"{bid}: fetched_at 缺失或不是带时区的 ISO 时间: {fa_raw!r}")
        else:
            if fa_dt > now + CLOCK_SKEW:
                errors.append(f"{bid}: fetched_at 在未来: {fa_raw}")
            if top_dt and fa_dt > top_dt + CLOCK_SKEW:
                errors.append(f"{bid}: fetched_at 晚于批次 last_fetched_at: {fa_raw} > {top_raw}")
            # 人工填写指纹：xx:00:00.000000 这类整分零微秒值，脚本几乎不可能生成
            if fa_dt.microsecond == 0 and fa_dt.second == 0:
                errors.append(f"{bid}: fetched_at 为整分零微秒（疑似手工填写）: {fa_raw}")
            seen_times[fa_raw] += 1

    for ts, n in seen_times.items():
        if n > 1:
            errors.append(f"{n} 条条目共享同一 fetched_at（抓取脚本每条间隔 ≥1s，不可能）: {ts}")
    if top_dt and top_raw in seen_times:
        errors.append(f"last_fetched_at 与 {seen_times[top_raw]} 条条目时间戳完全相同（疑似手工填写）: {top_raw}")

    if errors:
        print("PROVENANCE CHECK FAILED:")
        for e in errors:
            print(f"  - {e}")
        return False
    print(f"PROVENANCE CHECK PASSED: {len(bots)} 条 fetch 数据可溯源，"
          f"{len(seen_times)} 个互异抓取时间戳，批次 {top_raw[:10] if top_raw else '—'}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Validate bots data and pipeline state (M4/M5)")
    parser.add_argument("--check", choices=["seed", "readme", "links", "order", "dead", "notbot", "provenance"], help="Run specific check (default = all)")
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
        checks_to_run = ["seed", "readme", "links", "order", "dead", "notbot", "provenance"]
    else:
        checks_to_run = [args.check]

    for chk in checks_to_run:
        if chk == "seed":
            ok = check_seed(data) and ok
        elif chk == "readme":
            ok = check_readme(data, readme) and ok
        elif chk == "links":
            ok = check_links(data, readme) and ok
        elif chk == "order":
            ok = check_order(data, readme) and ok
        elif chk == "dead":
            ok = check_dead(data, readme) and ok
        elif chk == "notbot":
            ok = check_notbot(data, readme) and ok
        elif chk == "provenance":
            ok = check_provenance(data) and ok

    if args.check is None:
        if ok:
            print("FULL VALIDATION PASSED (all checks).")
        else:
            print("FULL VALIDATION FAILED (see above).")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
