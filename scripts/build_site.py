#!/usr/bin/env python3
"""把 data/bots.json 烘焙为 docs/index.html 静态站点。

页面结构位于 templates/index.html.j2，样式与浏览器脚本位于 docs/assets/。
数据全部预渲染进 HTML，无需运行时 fetch；页脚时间取 last_fetched_at，
因此数据不变时生成结果也不变。
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "bots.json"
OUT_FILE = ROOT / "docs" / "index.html"
TEMPLATE_DIR = ROOT / "templates"
AVATAR_DIR = ROOT / "docs" / "avatars"

CATEGORY_TITLES = {
    "official": ("官方账号", "Telegram 官方维护的建号、会员、贴纸、蓝标认证、解封申诉与客户端分发入口"),
    "search": ("搜索发现", "按关键词检索中文群组、频道、影视、网盘与音视频资源"),
    "group": ("群组管理", "拦截水军、外链广告与高频刷屏；中大型群组建议搭配「1 个进群验证 + 1 个广告拦截」组合使用"),
    "download": ("解析下载", "提取主流社媒与视频平台无水印内容，支持私聊发送链接或挂载至群内解析"),
    "ai": ("AI 助手", "多模型聚合对话与代码问答；优先选择支持长上下文与多模态输入的活跃账号"),
    "tools": ("实用工具", "拍卖提醒、跨格式文件转换、一次性临时邮箱、直链转存、PDF 处理与 RSS 订阅工具"),
    "translate": ("多语翻译", "私聊双向互译与群聊消息实时自动转译，适合多语种社群与跨国协作"),
    "checkin": ("签到打卡", "群内每日打卡、连续天数统计与考勤汇总，量化社群活跃度与团队出勤"),
    "channel": ("频道推送", "富媒体排版、定时发布队列、跨频道转发与评论/回应按钮，适合频道主日常运营"),
    "game": ("游戏娱乐", "群内实时抢答、棋牌对战、HTML5 小游戏与文字冒险，无需跳出聊天窗口即可发起互动"),
    "crypto": ("加密交易", "内建支付钱包与链上代币买卖；接入前用小额资金测试滑点与提现，并确认授权范围"),
}

CATEGORY_ORDER = ["official", "search", "crypto", "group", "download", "ai", "translate", "checkin", "channel", "game", "tools"]

HIDE_AFTER = 3  # keep in sync with scripts/fetch_bots.py

NOT_BOT_LABELS = {
    "channel": "已变更为频道 · 非 Bot",
    "group": "已变更为群组 · 非 Bot",
    "user": "个人账号 · 非 Bot",
}

SUBSECTION_TITLES = {
    "verify": "进群验证",
    "ads": "广告拦截",
    "stats": "活跃统计",
    "misc": "秩序维护",
}

UNITS = {"bot": "/月", "channel": " 订阅", "group": " 成员"}

TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(("html", "xml")),
    trim_blocks=True,
    lstrip_blocks=True,
)


def is_hidden(bot):
    fetch = bot.get("fetch", {}) or {}
    return fetch.get("status") == "dead" and int(fetch.get("dead_streak") or 0) >= HIDE_AFTER


def is_not_bot(bot):
    fetch = bot.get("fetch", {}) or {}
    return fetch.get("status") == "ok" and bool(fetch.get("not_bot"))


def sort_by_monthly(bots):
    """稳定排序：月活降序，无月活靠后，已失效最后（与 render_readme.py 规则一致）。"""
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


def format_verified_time(iso):
    """将 ISO 时间转换为 UTC 日期，保持构建结果可复现。"""
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")
    except ValueError:
        return iso[:10]


def format_num(n):
    if n is None:
        return "—"
    if n >= 100_000_000:
        return f"{n / 100_000_000:.1f} 亿"
    if n >= 10_000:
        return f"{n / 10_000:.1f} 万"
    return str(n)


def monthly_label(bot):
    fetch = bot.get("fetch", {}) or {}
    if fetch.get("status") == "dead":
        fa = fetch.get("fetched_at", "")
        ym = fa[:7] if fa else "—"
        return Markup(f'<span class="badge badge-dead">❗已失效（{ym}）</span>')
    users = fetch.get("monthly_users")
    if is_not_bot(bot):
        label = NOT_BOT_LABELS.get(fetch.get("page_kind"), "非 Bot 账号")
        kind = f'<span class="account-kind">{label}</span>'
        if not users:
            return Markup(kind)
        unit = UNITS.get(fetch.get("type") or "bot", "/月")
        return Markup(f'{kind}<span class="account-metric">{format_num(users)}{unit}</span>')
    if not users:
        return Markup('<span class="muted">—</span>')
    unit = UNITS.get(fetch.get("type") or "bot", "/月")
    return Markup(f'约 <strong>{format_num(users)}</strong>{unit}')


def clean_display_title(raw: str) -> str:
    s = re.sub(r"[🔍🤖🐴🇺🇦⚡️🎲🐰\ufe0f]+", "", raw)
    s = re.sub(r"\s*Powered by @[A-Za-z0-9_]+", "", s, flags=re.I)
    s = re.sub(r"\s*@[A-Za-z0-9_]+\s*$", "", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s


def display_name(bot):
    fetch = bot.get("fetch", {}) or {}
    override = (bot.get("display_name") or "").strip()
    if override:
        title = override
        if fetch.get("is_verified") or bot.get("official"):
            title = f'{title} <span class="verified">✓</span>'
        return Markup(title)
    raw_title = fetch.get("title") or bot.get("username", "").lstrip("@")
    title = clean_display_title(str(raw_title)) or str(raw_title).strip()
    if fetch.get("is_verified") or bot.get("official"):
        title = f'{title} <span class="verified">✓</span>'
    return Markup(title)


def url_field(bot):
    url = bot.get("url")
    if not url:
        return Markup('<span class="muted">—</span>')
    username = bot.get("username", "")
    return Markup(f'<a href="{url}" target="_blank" rel="noopener">{username}</a>')


def photo_url(bot):
    """整理头像地址。

    优先使用 scripts/fetch_avatars.py 抓取到 docs/avatars/ 的本地快照
    （telesco.pe 临时链接会过期，本地文件永不过期）；无本地快照时退回
    fetch.photo_url（仅接受 https）；都没有则输出空串，模板回退文字头像。
    """
    username = str(bot.get("username", "")).lstrip("@")
    if username and (AVATAR_DIR / f"{username}.jpg").is_file():
        return f"avatars/{username}.jpg"
    url = str((bot.get("fetch", {}) or {}).get("photo_url") or "").strip()
    return url if url.startswith("https://") else ""


def bot_view(bot):
    """把一条数据整理为模板所需的展示字段。"""
    fetch = bot.get("fetch", {}) or {}
    raw_title = str((bot.get("display_name") or "").strip() or fetch.get("title") or bot.get("username", "B").lstrip("@"))
    title = clean_display_title(raw_title) or raw_title.strip()
    category = bot.get("category", "")
    return {
        "name": display_name(bot),
        "initial": title[:1].upper() or "B",
        "username": bot.get("username", ""),
        "category_label": CATEGORY_TITLES.get(category, (category, ""))[0],
        "link_url": bot.get("url") or "",
        "url": url_field(bot),
        "notes": bot.get("notes", ""),
        "monthly": monthly_label(bot),
        "photo_url": photo_url(bot),
    }


def build_sections(by_cat):
    sections = []
    for cat in CATEGORY_ORDER:
        bots = by_cat.get(cat, [])
        if not bots:
            continue
        title, desc = CATEGORY_TITLES[cat]
        if cat == "group":
            groups = []
            for sub_key in ("verify", "ads", "stats", "misc"):
                sub_bots = sort_by_monthly([
                    b for b in bots if (b.get("subsection") or "misc") == sub_key
                ])
                if sub_bots:
                    groups.append({
                        "title": SUBSECTION_TITLES.get(sub_key, sub_key),
                        "bots": [bot_view(b) for b in sub_bots],
                    })
        else:
            groups = [{
                "title": None,
                "bots": [bot_view(b) for b in sort_by_monthly(bots)],
            }]
        sections.append({"key": cat, "title": title, "desc": desc, "count": len(bots), "groups": groups})
    return sections


def rank_top(pool, limit):
    """按公开月活降序取前 N 条，附带格式化后的月活与单位。"""
    top = sorted(pool, key=lambda b: -b["fetch"]["monthly_users"])[:limit]
    return [{
        **bot_view(bot),
        "users": format_num(bot["fetch"]["monthly_users"]),
        "unit": UNITS.get(bot["fetch"].get("type", "bot"), "/月"),
    } for bot in top]


def build_top10(bots):
    # 官方账号月活天然巨大，榜单只排第三方 bot。
    pool = [
        b for b in bots
        if b.get("fetch", {}).get("monthly_users")
        and not is_not_bot(b)
        and b.get("category") != "official"
    ]
    return rank_top(pool, 10)


def build_search_top(bots, limit=3):
    """首屏速览面板：搜索分类内按公开月活取前 N 条。"""
    pool = [
        b for b in bots
        if b.get("category") == "search"
        and b.get("fetch", {}).get("monthly_users")
        and not is_not_bot(b)
    ]
    return rank_top(pool, limit)


def build_context(data):
    bots = [b for b in data.get("bots", []) if not is_hidden(b)]
    by_cat = {}
    for bot in bots:
        cat = bot.get("category")
        # 精选条目同样在所属分类中列出。
        if cat in CATEGORY_TITLES:
            by_cat.setdefault(cat, []).append(bot)

    featured = sort_by_monthly([b for b in bots if b.get("featured")])
    return {
        "total": len(bots),
        "ok_count": sum(
            1 for b in bots
            if b.get("fetch", {}).get("status") == "ok" and not is_not_bot(b)
        ),
        "last_label": data.get("last_verified_label") or (data.get("last_fetched_at", "")[:7] or "—"),
        "cat_count": sum(1 for cat in CATEGORY_ORDER if by_cat.get(cat)),
        "verified_time": format_verified_time(data.get("last_fetched_at")),
        "featured": [bot_view(b) for b in featured],
        "top10": build_top10(bots),
        "search_top": build_search_top(bots),
        "sections": build_sections(by_cat),
    }


def build_html(data):
    template = TEMPLATE_ENV.get_template("index.html.j2")
    return template.render(**build_context(data))


def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    html = build_html(data)
    if OUT_FILE.exists() and OUT_FILE.read_text(encoding="utf-8") == html:
        print(f"Site unchanged: {OUT_FILE}")
    else:
        OUT_FILE.write_text(html, encoding="utf-8")
        print(f"Site built: {OUT_FILE}")
    print(f"  - Total bots shown: {sum(1 for b in data.get('bots', []) if not is_hidden(b))}")
    print(f"  - Featured: {sum(1 for b in data.get('bots', []) if b.get('featured'))}")
    print(f"  - Output size: {OUT_FILE.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
