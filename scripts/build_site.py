#!/usr/bin/env python3
"""
build_site.py - 把 data/bots.json 烘焙为 docs/index.html 静态站点。

设计系统适配自 codertesla.github.io 的霓虹深色玻璃拟态风：
- 深色背景 (#030303) + 霓虹色 (cyan/purple/green)
- Inter / Outfit 字体
- 玻璃卡片 + 渐变标题 + 背景光斑
- 客户端搜索 / 分类筛选 (vanilla JS)
- 数据全部预渲染进 HTML，无需运行时 fetch
- 输出只依赖 bots.json（页脚时间取 last_fetched_at，而非构建时间），
  数据不变则 docs/index.html 不变，不会产生无意义 diff
- fetch.dead_streak >= HIDE_AFTER 的条目隐藏；not_bot 条目加 ⚠️ 标记
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "bots.json"
OUT_FILE = ROOT / "docs" / "index.html"

CATEGORY_TITLES = {
    "official": ("官方账号", "Telegram 官方维护的建号、会员、贴纸、蓝标认证、解封申诉与客户端分发入口"),
    "search": ("搜索发现", "按关键词检索中文群组、频道、影视、网盘与音视频资源"),
    "group": ("群组管理", "拦截水军、外链广告与高频刷屏；中大型群组建议搭配「1 个进群验证 + 1 个广告拦截」组合使用"),
    "download": ("解析下载", "提取主流社媒与视频平台无水印内容，支持私聊发送链接或挂载至群内解析"),
    "ai": ("AI 助手", "AI 对话机器人迭代极快，建议在 Telegram 内直接检索当月活跃账号"),
    "tools": ("实用工具", "一次性临时邮箱、词典、天气、安装包提取与群内抽奖工具"),
    "translate": ("多语翻译", "私聊双向互译与群聊消息实时自动转译，适合多语种社群与跨国协作"),
    "checkin": ("签到打卡", "群内每日打卡、连续天数统计与考勤汇总，量化社群活跃度与团队出勤"),
    "channel": ("频道推送", "富媒体排版、定时发布队列与跨频道规则转发，适合频道主日常运营"),
    "game": ("游戏娱乐", "群内实时抢答、HTML5 对战小游戏与文字冒险，无需跳出聊天窗口即可发起互动"),
    "crypto": ("加密交易", "在 Telegram 内直接看行情、跟单与买卖链上代币，适合 Solana 等公链的高频交易"),
}

CATEGORY_ORDER = ["official", "search", "crypto", "group", "download", "ai", "translate", "checkin", "channel", "game", "tools"]

HIDE_AFTER = 3  # keep in sync with scripts/fetch_bots.py

NOT_BOT_LABELS = {
    "channel": "⚠️已变为频道（非 Bot）",
    "group": "⚠️已变为群组（非 Bot）",
    "user": "⚠️个人账号（非 Bot）",
}


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
    """'2026-10-12T04:00:00+00:00' -> '2026-10-12' (UTC date; deterministic, from data)."""
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")
    except ValueError:
        return iso[:10]


SUBSECTION_TITLES = {
    "verify": "进群验证",
    "ads": "广告拦截",
    "stats": "活跃统计",
    "misc": "秩序维护",
}


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
        return f'<span class="badge badge-dead">❗已失效（{ym}）</span>'
    users = fetch.get("monthly_users")
    if is_not_bot(bot):
        label = NOT_BOT_LABELS.get(fetch.get("page_kind"), "⚠️非 Bot")
        badge = f'<span class="badge badge-dead">{label}</span>'
        if not users:
            return badge
        unit = {"bot": "/月", "channel": " 订阅", "group": " 成员"}.get(fetch.get("type") or "bot", "/月")
        return f'{badge}<br><strong>{format_num(users)}</strong>{unit.lstrip()}'
    if not users:
        return '<span class="muted">—</span>'
    typ = fetch.get("type") or "bot"
    unit = {"bot": "/月", "channel": " 订阅", "group": " 成员"}.get(typ, "/月")
    return f'约 <strong>{format_num(users)}</strong>{unit}'


def clean_display_title(raw: str) -> str:
    import re
    s = re.sub(r"[🔍🤖🐴🇺🇦⚡️🎲🐰\ufe0f]+", "", raw)
    s = re.sub(r"\s*Powered by @[A-Za-z0-9_]+", "", s, flags=re.I)
    s = re.sub(r"\s*@[A-Za-z0-9_]+\s*$", "", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s


def display_name(bot):
    fetch = bot.get("fetch", {}) or {}
    raw_title = fetch.get("title") or bot.get("username", "").lstrip("@")
    title = clean_display_title(str(raw_title)) or str(raw_title).strip()
    if fetch.get("is_verified") or bot.get("official"):
        title = f'{title} <span class="verified">✓</span>'
    return title


def url_field(bot):
    url = bot.get("url")
    if not url:
        return '<span class="muted">—</span>'
    username = bot.get("username", "")
    return f'<a href="{url}" target="_blank" rel="noopener">{username}</a>'


def notes_field(bot):
    return bot.get("notes", "")


def render_bot_row(bot):
    name = display_name(bot)
    url = url_field(bot)
    notes = notes_field(bot)
    monthly = monthly_label(bot)
    return f"""      <tr>
        <td class="col-name">{name}</td>
        <td class="col-link">{url}</td>
        <td class="col-notes">{notes}</td>
        <td class="col-monthly">{monthly}</td>
      </tr>"""


def render_category_table(bots):
    if not bots:
        return '<p class="muted">暂无收录。</p>'
    rows = "\n".join(render_bot_row(b) for b in bots)
    return f"""    <div class="table-wrap">
      <table class="bot-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>链接</th>
            <th>核心功能</th>
            <th>月活</th>
          </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </div>"""


def render_group_section(bots):
    """群管类按 subsection 分组渲染 4 个小表；组内按月活降序。"""
    parts = []
    for sub_key in ["verify", "ads", "stats", "misc"]:
        sub_bots = sort_by_monthly([b for b in bots if (b.get("subsection") or "misc") == sub_key])
        if not sub_bots:
            continue
        title = SUBSECTION_TITLES.get(sub_key, sub_key)
        parts.append(f'    <h3 class="subsection-title">{title}</h3>')
        parts.append(render_category_table(sub_bots))
    return "\n".join(parts)


def render_category_section(cat, bots):
    title, desc = CATEGORY_TITLES.get(cat, (cat, ""))
    if cat == "group":
        body = render_group_section(bots)
    else:
        body = render_category_table(sort_by_monthly(bots))
    return f"""  <section class="category-section" id="cat-{cat}" data-category="{cat}">
    <h2 class="section-heading">{title}</h2>
    <p class="category-desc">{desc}</p>
{body}
  </section>"""


def render_top10(bots):
    # 官方号月活天然巨大（SpamBot 3400 万+），全量榜会被它们霸占 4 席，
    # 因此榜单只排第三方 bot，官方入口统一放在官方分类。
    pool = [b for b in bots
            if b.get("fetch", {}).get("monthly_users")
            and not is_not_bot(b)
            and b.get("category") != "official"]
    top = sorted(pool, key=lambda b: -b["fetch"]["monthly_users"])[:10]
    if not top:
        return ""
    items = []
    for i, b in enumerate(top, 1):
        fetch = b.get("fetch", {})
        users = fetch.get("monthly_users", 0)
        typ = fetch.get("type", "bot")
        unit = {"bot": "/月", "channel": " 订阅", "group": " 成员"}.get(typ, "/月")
        name = display_name(b)
        url = url_field(b)
        items.append(f"""      <li class="top-item rank-{i}">
        <span class="rank">{i}</span>
        <span class="top-name">{name}</span>
        <span class="top-link">{url}</span>
        <span class="top-monthly">约 <strong>{format_num(users)}</strong>{unit}</span>
      </li>""")
    return f"""  <section class="top10-section" id="top10">
    <h2 class="section-heading">月活 Top 10</h2>
    <p class="category-desc">本列表中第三方 bot 按 Telegram 公开月活数据排名的前 10 名（每周自动核验，官方账号另见官方分类）</p>
    <ol class="top-list">
{chr(10).join(items)}
    </ol>
  </section>"""


def render_featured(featured_bots):
    if not featured_bots:
        return ""
    cards = []
    for b in sort_by_monthly(featured_bots):
        fetch = b.get("fetch", {})
        name = display_name(b)
        url = url_field(b)
        notes = notes_field(b)
        monthly = monthly_label(b)
        cards.append(f"""      <div class="featured-card">
        <div class="featured-name">{name}</div>
        <div class="featured-link">{url}</div>
        <div class="featured-notes">{notes}</div>
        <div class="featured-monthly">{monthly}</div>
      </div>""")
    cards_html = "\n".join(cards)
    return f"""  <section class="featured-section" id="featured">
    <h2 class="section-heading">精选必装</h2>
    <p class="category-desc">覆盖 5 个最高频使用场景的入口（官方 / 搜索 / 群管 / 下载 / 娱乐），每个场景只放该分类月活最高、确认在运营的一个</p>
    <div class="featured-grid">
{cards_html}
    </div>
  </section>"""


def build_html(data):
    bots = [b for b in data.get("bots", []) if not is_hidden(b)]
    featured = [b for b in bots if b.get("featured")]
    by_cat = {}
    for b in bots:
        cat = b.get("category")
        # 分类保持完整：精选里的条目（含官方入口）同样在所属分类再列一次
        if cat in CATEGORY_TITLES:
            by_cat.setdefault(cat, []).append(b)

    total = len(bots)
    ok_count = sum(1 for b in bots if b.get("fetch", {}).get("status") == "ok" and not is_not_bot(b))
    last_label = data.get("last_verified_label") or (data.get("last_fetched_at", "")[:7] or "—")

    # 只统计真正有内容的分类（空分类不渲染，AI 目前为空）
    cat_count = sum(1 for cat in CATEGORY_ORDER if by_cat.get(cat))

    featured_html = render_featured(featured)
    top10_html = render_top10(bots)
    cat_sections = "\n".join(
        render_category_section(cat, by_cat.get(cat, [])) for cat in CATEGORY_ORDER if by_cat.get(cat)
    )

    verified_time = format_verified_time(data.get("last_fetched_at"))

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>电报机器人大全 | 精选实用 Telegram Bot 推荐（{last_label}）</title>
  <meta name="description" content="中文 Telegram 机器人导航列表：{total} 条精选 bot，带真实月活数据，每周自动核验失效。覆盖官方、搜索、群管、下载、AI、翻译、签到、频道推送、游戏、工具 11 大分类。">
  <meta name="keywords" content="电报机器人,Telegram 机器人,TG 机器人,Telegram Bot 推荐,群管理机器人,中文 TG Bot">
  <meta property="og:title" content="电报机器人大全 | 精选实用 Telegram Bot 推荐">
  <meta property="og:description" content="{total} 条精选中文 Telegram Bot，带真实月活数据，每周自动核验失效。">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://codertesla.github.io/telegram-bots/">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="canonical" href="https://codertesla.github.io/telegram-bots/">
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
  <style>
:root {{
  /* Editorial Dark (synced with portfolio) */
  --bg-color: #0a0a0a;
  --card-bg: #161616;
  --text-primary: #ededed;
  --text-secondary: #9a9a9a;
  --border: rgba(255, 255, 255, 0.08);
  --accent: #e8b04d;
  --accent-hover: #f5d68a;
  --error: #ef4444;

  /* Typography */
  --font-heading: 'Space Grotesk', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-main: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;

  --transition-smooth: border-color 0.2s ease, background-color 0.2s ease, color 0.2s ease;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  background-color: var(--bg-color);
  color: var(--text-primary);
  font-family: var(--font-main);
  line-height: 1.65;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
}}
a {{ color: var(--accent); text-decoration: none; transition: var(--transition-smooth); }}
a:hover {{ color: var(--accent-hover); text-decoration: underline; }}
.muted {{ color: var(--text-secondary); }}
.verified {{ color: var(--accent); font-weight: 700; }}
.badge {{ font-size: 0.8rem; padding: 2px 8px; border-radius: 6px; }}
.badge-dead {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}

/* Header */
header {{
  padding: 1rem 0;
  display: flex; justify-content: space-between; align-items: center;
  position: sticky; top: 0; z-index: 1000;
  background: #0a0a0a;
  border-bottom: 1px solid var(--border);
}}
.container {{ max-width: 1200px; margin: 0 auto; padding: 0 1.5rem; }}
.logo {{
  font-family: var(--font-heading);
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}}
nav ul {{ list-style: none; display: flex; gap: 1rem; flex-wrap: wrap; }}
nav a {{ color: var(--text-secondary); font-size: 0.9rem; }}
nav a:hover {{ color: var(--accent); text-decoration: none; }}

/* Search */
.search-wrap {{
  position: sticky; top: 56px; z-index: 999;
  background: #0a0a0a;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border);
}}
.search-box {{
  width: 100%; max-width: 600px; margin: 0 auto; display: block;
  padding: 0.65rem 1rem; font-size: 0.95rem; font-family: var(--font-main);
  background: var(--card-bg); border: 1px solid var(--border); border-radius: 999px;
  color: var(--text-primary); outline: none; transition: var(--transition-smooth);
}}
.search-box:focus {{ border-color: var(--accent); }}
.search-box::placeholder {{ color: var(--text-secondary); }}

/* Hero - subtle radial only */
.hero {{
  padding: 5rem 0 4rem;
  text-align: center;
  background: radial-gradient(ellipse at 50% 0%, rgba(232,176,77,0.06), transparent 60%);
}}
.hero h1 {{
  font-family: var(--font-heading);
  font-size: clamp(2.5rem, 6vw, 4rem);
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: 1rem;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}}
.hero p {{ font-size: 1.1rem; color: var(--text-secondary); max-width: 640px; margin: 0 auto 2rem; }}
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem; max-width: 700px; margin: 0 auto 2rem; }}
.stat-card {{
  background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 1rem;
  transition: var(--transition-smooth);
}}
.stat-card:hover {{ border-color: rgba(232,176,77,0.4); background: #1a1a1a; }}
.stat-num {{
  font-family: var(--font-heading);
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent);
}}
.stat-label {{ font-size: 0.8rem; color: rgba(255,255,255,0.6); margin-top: 0.25rem; }}
.hero-actions {{ display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }}
.btn {{
  display: inline-block; padding: 0.7rem 1.5rem; font-weight: 600; border-radius: 6px;
  background: var(--accent); color: #0a0a0a; border: none; cursor: pointer;
  font-size: 0.95rem; transition: var(--transition-smooth);
}}
.btn:hover {{ background: var(--accent-hover); text-decoration: none; }}
.btn-outline {{
  background: transparent; border: 1px solid rgba(255,255,255,0.15); color: var(--text-primary);
}}
.btn-outline:hover {{ border-color: var(--accent); color: var(--accent); background: transparent; }}

/* Section */
section {{ padding: 4rem 0 3rem; }}
.section-heading {{
  font-family: var(--font-heading);
  font-size: 1.75rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  position: relative;
  display: inline-block;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}}
.section-heading::after {{
  content: ''; position: absolute; bottom: -10px; left: 0; width: 40px; height: 3px;
  background: var(--accent); border-radius: 2px;
}}
.category-desc {{ color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 1.5rem; }}

/* Featured cards */
.featured-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }}
.featured-card {{
  background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 1.25rem;
  transition: var(--transition-smooth);
}}
.featured-card:hover {{ border-color: rgba(232,176,77,0.4); background: #1a1a1a; }}
.featured-name {{
  font-family: var(--font-heading);
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}}
.featured-link {{ font-size: 0.9rem; margin-bottom: 0.5rem; }}
.featured-notes {{ color: var(--text-secondary); font-size: 0.88rem; margin-bottom: 0.5rem; }}
.featured-monthly {{ font-size: 0.85rem; color: var(--accent); }}

/* Top 10 list */
.top-list {{ list-style: none; padding: 0; }}
.top-item {{
  display: grid; grid-template-columns: 40px 1fr auto auto; gap: 1.25rem; align-items: center;
  padding: 0.9rem 1rem; margin-bottom: 0.5rem; border-radius: 12px;
  background: var(--card-bg); border: 1px solid var(--border); transition: var(--transition-smooth);
}}
.top-item:hover {{ border-color: rgba(232,176,77,0.4); background: #1a1a1a; }}
.top-item.rank-1 {{ border-color: rgba(232,176,77,0.35); }}
.top-item.rank-2 {{ border-color: rgba(232,176,77,0.22); }}
.top-item.rank-3 {{ border-color: rgba(232,176,77,0.15); }}
.rank {{
  font-family: var(--font-heading);
  font-size: 1.35rem;
  font-weight: 700;
  text-align: center;
  color: var(--accent);
}}
.top-name {{ font-weight: 600; color: var(--text-primary); }}
.top-link {{ font-size: 0.85rem; }}
.top-monthly {{ font-size: 0.85rem; color: var(--accent); white-space: nowrap; }}

/* Bot table */
.table-wrap {{ overflow-x: auto; border-radius: 12px; border: 1px solid var(--border); }}
.bot-table {{ width: 100%; border-collapse: collapse; min-width: 600px; }}
.bot-table th {{
  text-align: left; padding: 0.9rem 1rem; font-size: 0.85rem; font-weight: 600;
  color: var(--text-secondary); background: rgba(255,255,255,0.02);
  border-bottom: 1px solid var(--border); position: sticky; top: 0;
}}
.bot-table td {{ padding: 0.9rem 1rem; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.9rem; vertical-align: top; }}
.bot-table tr {{ transition: var(--transition-smooth); }}
.bot-table tbody tr:hover {{ background: rgba(255,255,255,0.015); }}
.bot-table tr:last-child td {{ border-bottom: none; }}
.col-name {{ font-weight: 600; white-space: nowrap; color: var(--text-primary); }}
.col-link {{ white-space: nowrap; }}
.col-monthly {{ white-space: nowrap; color: var(--accent); }}
.subsection-title {{
  font-family: var(--font-heading);
  font-size: 1.15rem;
  font-weight: 600;
  margin: 1.75rem 0 0.75rem;
  color: var(--accent);
}}

/* Footer - improved spacing (task 3) */
footer {{
  padding: 4rem 0 3rem;
  border-top: 1px solid var(--border);
  margin-top: 3rem;
}}
.footer-content {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}}
footer p {{ color: var(--text-secondary); font-size: 0.85rem; }}
.footer-links {{ display: flex; gap: 1rem; }}
.footer-links a {{ color: var(--text-secondary); }}
.footer-links a:hover {{ color: var(--accent); text-decoration: none; }}

/* Search filter: hide non-matching rows */
.bot-table tr.is-hidden {{ display: none; }}
.category-section.is-hidden {{ display: none; }}
.featured-card.is-hidden {{ display: none; }}
.top-item.is-hidden {{ display: none; }}

/* Responsive */
@media (max-width: 768px) {{
  .hero {{ padding: 3.5rem 0 3rem; }}
  .top-item {{ grid-template-columns: 30px 1fr; gap: 0.5rem; }}
  .top-link, .top-monthly {{ grid-column: 2; }}
  .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
  nav ul {{ gap: 0.6rem; }}
  nav a {{ font-size: 0.8rem; }}
}}

@media (prefers-reduced-motion: reduce) {{
  html {{ scroll-behavior: auto; }}
  .featured-card:hover, .top-item:hover, .stat-card:hover, .btn:hover {{ transform: none; }}
}}
  </style>
</head>
<body>
  <header>
    <div class="container" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
      <a href="/" class="logo">电报机器人大全</a>
      <nav>
        <ul>
          <li><a href="#featured">精选</a></li>
          <li><a href="#top10">Top 10</a></li>
          <li><a href="#cat-official">官方</a></li>
          <li><a href="#cat-search">搜索</a></li>
          <li><a href="#cat-group">群管</a></li>
          <li><a href="#cat-download">下载</a></li>
          <li><a href="#cat-translate">翻译</a></li>
          <li><a href="#cat-game">游戏</a></li>
          <li><a href="https://github.com/codertesla/telegram-bots" target="_blank" rel="noopener">GitHub ↗</a></li>
        </ul>
      </nav>
    </div>
  </header>

  <div class="search-wrap">
    <div class="container">
      <input type="text" class="search-box" id="search" placeholder="🔍 搜索机器人名称、关键词、用户名..." aria-label="搜索机器人">
    </div>
  </div>

  <main class="container">
    <section class="hero">
      <h1>中文 Telegram 机器人导航</h1>
      <p>精选 {total} 条活跃电报机器人，按 {cat_count} 大场景分类组织，每条带真实月活数据，每周由 GitHub Actions 自动核验失效。</p>
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-num">{total}</div><div class="stat-label">收录 Bot</div></div>
        <div class="stat-card"><div class="stat-num">{cat_count}</div><div class="stat-label">分类</div></div>
        <div class="stat-card"><div class="stat-num">{ok_count}</div><div class="stat-label">活跃中</div></div>
        <div class="stat-card"><div class="stat-num">{last_label}</div><div class="stat-label">最近核验</div></div>
      </div>
      <div class="hero-actions">
        <a href="#featured" class="btn">浏览精选</a>
        <a href="https://github.com/codertesla/telegram-bots" target="_blank" rel="noopener" class="btn btn-outline">查看 GitHub</a>
      </div>
    </section>

{featured_html}

{top10_html}

{cat_sections}
  </main>

  <footer>
    <div class="container">
      <div class="footer-content">
        <p>电报机器人大全 · 数据来自 Telegram 公开预览页 · 每周自动核验<br>数据核验于 {verified_time}</p>
        <div class="footer-links">
          <a href="https://github.com/codertesla/telegram-bots" target="_blank" rel="noopener">GitHub</a>
          <a href="https://github.com/codertesla/telegram-bots/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener">贡献指南</a>
          <a href="https://github.com/codertesla/telegram-bots/issues/new/choose" target="_blank" rel="noopener">推荐 Bot</a>
        </div>
      </div>
    </div>
  </footer>

  <script>
    // 客户端搜索：实时过滤表格行 + 隐藏空分类区
    const search = document.getElementById('search');
    const sections = document.querySelectorAll('.category-section');
    const topItems = document.querySelectorAll('.top-item');

    search.addEventListener('input', (e) => {{
      const q = e.target.value.trim().toLowerCase();
      if (!q) {{
        document.querySelectorAll('.is-hidden').forEach(el => el.classList.remove('is-hidden'));
        return;
      }}
      sections.forEach(sec => {{
        let visibleRows = 0;
        sec.querySelectorAll('tbody tr').forEach(row => {{
          const text = row.textContent.toLowerCase();
          if (text.includes(q)) {{
            row.classList.remove('is-hidden');
            visibleRows++;
          }} else {{
            row.classList.add('is-hidden');
          }}
        }});
        // Hide section if no matching rows
        if (visibleRows === 0) {{
          sec.classList.add('is-hidden');
        }} else {{
          sec.classList.remove('is-hidden');
        }}
      }});
      // Filter top 10 list too
      topItems.forEach(item => {{
        const text = item.textContent.toLowerCase();
        item.classList.toggle('is-hidden', !text.includes(q));
      }});
      // Featured cards
      document.querySelectorAll('.featured-card').forEach(card => {{
        const text = card.textContent.toLowerCase();
        card.classList.toggle('is-hidden', !text.includes(q));
      }});
    }});
  </script>
</body>
</html>"""


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
