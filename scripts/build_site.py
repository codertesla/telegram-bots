#!/usr/bin/env python3
"""
build_site.py - 把 data/bots.json 烘焙为 docs/index.html 静态站点。

设计系统适配自 codertesla.github.io 的霓虹深色玻璃拟态风：
- 深色背景 (#030303) + 霓虹色 (cyan/purple/green)
- Inter / Outfit 字体
- 玻璃卡片 + 渐变标题 + 背景光斑
- 客户端搜索 / 分类筛选 (vanilla JS)
- 数据全部预渲染进 HTML，无需运行时 fetch
"""
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "bots.json"
OUT_FILE = ROOT / "docs" / "index.html"

CATEGORY_TITLES = {
    "search": ("Telegram 搜索与发现类机器人", "🔍 用于查找群组、频道、视频、音乐、文件等资源"),
    "group": ("Telegram 群组管理与安全类机器人", "🛡️ 防止水军、广告、刷屏；建议 1-2 个验证类 + 1 个拦截类组合使用"),
    "download": ("资源解析与下载类机器人", "🎬 支持多平台内容获取（请遵守相关平台版权规定）"),
    "ai": ("AI 智能类电报机器人", "🤖 AI 对话机器人，迭代极快，建议在 Telegram 内搜索最新活跃账号"),
    "rss": ("通知订阅类 Telegram 机器人", "📡 RSS 全文订阅与关键词过滤"),
    "tools": ("实用工具类 Telegram 机器人", "🛠️ 临时邮箱、词典、天气、抽奖等杂项工具"),
    "translate": ("翻译类 Telegram 机器人", "🌍 中英文互译、群消息实时自动翻译、多语言支持"),
    "checkin": ("签到打卡类电报机器人", "✅ 社群签到、打卡统计、连续天数与积分排行"),
    "channel": ("频道推送类 Telegram 机器人", "📤 管理 Telegram 频道、定时发布、自动转发与订阅索引"),
    "game": ("游戏娱乐类电报机器人", "🎮 群内小游戏、单人休闲、互动娱乐"),
}

CATEGORY_ORDER = ["search", "group", "download", "ai", "rss", "translate", "checkin", "channel", "game", "tools"]

SUBSECTION_TITLES = {
    "verify": "进群验证类",
    "ads": "广告与水军拦截类",
    "stats": "统计与监控类",
    "misc": "其他实用",
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
    if not users:
        return '<span class="muted">—</span>'
    typ = fetch.get("type") or "bot"
    unit = {"bot": "/月", "channel": " 订阅", "group": " 成员"}.get(typ, "/月")
    return f'约 <strong>{format_num(users)}</strong>{unit}'


def display_name(bot):
    fetch = bot.get("fetch", {}) or {}
    title = fetch.get("title") or bot.get("username", "").lstrip("@")
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
    """群管类按 subsection 分组渲染 4 个小表。"""
    parts = []
    for sub_key in ["verify", "ads", "stats", "misc"]:
        sub_bots = [b for b in bots if (b.get("subsection") or "misc") == sub_key]
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
        body = render_category_table(bots)
    return f"""  <section class="category-section" id="cat-{cat}" data-category="{cat}">
    <h2 class="section-heading">{title}</h2>
    <p class="category-desc">{desc}</p>
{body}
  </section>"""


def render_top10(bots):
    top = sorted(
        [b for b in bots if b.get("fetch", {}).get("monthly_users")],
        key=lambda b: -b["fetch"]["monthly_users"],
    )[:10]
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
    <p class="category-desc">本列表中按 Telegram 公开月活数据排名的前 10 名（每周自动核验）</p>
    <ol class="top-list">
{chr(10).join(items)}
    </ol>
  </section>"""


def render_featured(featured_bots):
    if not featured_bots:
        return ""
    cards = []
    for b in featured_bots:
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
    <p class="category-desc">覆盖 5 个最高频使用场景的入口（官方 / 搜索 / 群管 / RSS / 下载）</p>
    <div class="featured-grid">
{cards_html}
    </div>
  </section>"""


def build_html(data):
    bots = data.get("bots", [])
    featured = [b for b in bots if b.get("featured")]
    non_featured = [b for b in bots if not b.get("featured")]

    by_cat = {}
    for b in non_featured:
        cat = b.get("category")
        if cat in CATEGORY_TITLES:
            by_cat.setdefault(cat, []).append(b)

    total = len(bots)
    ok_count = sum(1 for b in bots if b.get("fetch", {}).get("status") == "ok")
    last_label = data.get("last_verified_label") or (data.get("last_fetched_at", "")[:7] or "—")

    featured_html = render_featured(featured)
    top10_html = render_top10(bots)
    cat_sections = "\n".join(
        render_category_section(cat, by_cat.get(cat, [])) for cat in CATEGORY_ORDER if by_cat.get(cat)
    )

    build_time = datetime.now(tz=__import__("datetime").timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>电报机器人大全 | 精选实用 Telegram Bot 推荐（{last_label}）</title>
  <meta name="description" content="中文 Telegram 机器人导航列表：{total} 条精选 bot，带真实月活数据，每周自动核验失效。覆盖搜索、群管、下载、AI、RSS、翻译、签到、频道推送、游戏、工具 10 大分类。">
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
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Outfit:wght@300;400;700;900&display=swap" rel="stylesheet">
  <style>
:root {{
  --bg-color: #030303;
  --text-color: #f5f5f7;
  --accent-cyan: #00f2ff;
  --accent-purple: #bc13fe;
  --accent-green: #4ade80;
  --accent-orange: #fb923c;
  --glass-bg: rgba(255, 255, 255, 0.05);
  --glass-border: rgba(255, 255, 255, 0.1);
  --font-main: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-brand: 'Outfit', 'Inter', sans-serif;
  --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  background-color: var(--bg-color);
  color: var(--text-color);
  font-family: var(--font-main);
  line-height: 1.6;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
}}
a {{ color: var(--accent-cyan); text-decoration: none; transition: var(--transition); }}
a:hover {{ color: #fff; text-decoration: underline; }}
.muted {{ color: rgba(255,255,255,0.4); }}
.verified {{ color: var(--accent-cyan); font-weight: 700; }}
.badge {{ font-size: 0.8rem; padding: 2px 8px; border-radius: 6px; }}
.badge-dead {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}

/* Background blobs */
.bg-blobs {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; filter: blur(80px); opacity: 0.35; pointer-events: none; }}
.blob {{ position: absolute; border-radius: 50%; }}
.blob-1 {{ width: 400px; height: 400px; background: var(--accent-cyan); top: -100px; left: -100px; animation: move 20s infinite alternate; }}
.blob-2 {{ width: 500px; height: 500px; background: var(--accent-purple); bottom: -150px; right: -150px; animation: move 25s infinite alternate-reverse; }}
.blob-3 {{ width: 350px; height: 350px; background: var(--accent-green); top: 40%; left: 60%; animation: move 30s infinite alternate; opacity: 0.5; }}
@keyframes move {{ from {{ transform: translate(0, 0); }} to {{ transform: translate(120px, 120px); }} }}

/* Header */
header {{
  padding: 1rem 0;
  display: flex; justify-content: space-between; align-items: center;
  position: sticky; top: 0; z-index: 1000;
  backdrop-filter: blur(10px); background: rgba(3, 3, 3, 0.75);
  border-bottom: 1px solid var(--glass-border);
}}
.container {{ max-width: 1200px; margin: 0 auto; padding: 0 1.5rem; }}
.logo {{
  font-family: var(--font-brand); font-size: 1.35rem; font-weight: 800;
  background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}}
nav ul {{ list-style: none; display: flex; gap: 1rem; flex-wrap: wrap; }}
nav a {{ color: rgba(255,255,255,0.7); font-size: 0.9rem; }}
nav a:hover {{ color: var(--accent-cyan); text-decoration: none; }}

/* Search */
.search-wrap {{ position: sticky; top: 64px; z-index: 999; background: rgba(3,3,3,0.85); backdrop-filter: blur(10px); padding: 0.75rem 0; border-bottom: 1px solid var(--glass-border); }}
.search-box {{
  width: 100%; max-width: 600px; margin: 0 auto; display: block;
  padding: 0.65rem 1rem; font-size: 0.95rem; font-family: var(--font-main);
  background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 999px;
  color: var(--text-color); outline: none; transition: var(--transition);
}}
.search-box:focus {{ border-color: var(--accent-cyan); box-shadow: 0 0 0 3px rgba(0,242,255,0.15); }}
.search-box::placeholder {{ color: rgba(255,255,255,0.4); }}

/* Hero */
.hero {{ padding: 5rem 0 3rem; text-align: center; }}
.hero h1 {{
  font-family: var(--font-brand); font-size: clamp(2.5rem, 6vw, 4rem); font-weight: 800;
  line-height: 1.1; margin-bottom: 1rem;
  background: linear-gradient(135deg, #fff 0%, var(--accent-cyan) 60%, var(--accent-purple) 100%);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}}
.hero p {{ font-size: 1.1rem; color: rgba(255,255,255,0.7); max-width: 640px; margin: 0 auto 2rem; }}
.hero-emergency {{
  display: inline-block; padding: 0.6rem 1.2rem; margin-bottom: 2rem; font-size: 0.85rem;
  background: rgba(251, 146, 60, 0.1); border: 1px solid rgba(251, 146, 60, 0.3); border-radius: 12px;
  color: var(--accent-orange);
}}
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem; max-width: 700px; margin: 0 auto 2rem; }}
.stat-card {{
  background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 16px; padding: 1rem;
  transition: var(--transition);
}}
.stat-card:hover {{ border-color: var(--accent-cyan); transform: translateY(-3px); }}
.stat-num {{
  font-family: var(--font-brand); font-size: 2rem; font-weight: 800;
  background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}}
.stat-label {{ font-size: 0.8rem; color: rgba(255,255,255,0.6); margin-top: 0.25rem; }}
.hero-actions {{ display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }}
.btn {{
  display: inline-block; padding: 0.7rem 1.5rem; font-weight: 600; border-radius: 30px;
  background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple)); color: #fff;
  border: none; cursor: pointer; transition: var(--transition);
}}
.btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,242,255,0.3); text-decoration: none; }}
.btn-outline {{ background: transparent; border: 1px solid var(--glass-border); color: #fff; }}
.btn-outline:hover {{ border-color: var(--accent-cyan); background: rgba(0,242,255,0.05); }}

/* Section */
section {{ padding: 3rem 0; }}
.section-heading {{
  font-family: var(--font-brand); font-size: 1.75rem; font-weight: 700; margin-bottom: 0.5rem;
  position: relative; display: inline-block; padding-bottom: 0.5rem;
}}
.section-heading::after {{
  content: ''; position: absolute; bottom: 0; left: 0; width: 60px; height: 3px;
  background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple)); border-radius: 2px;
}}
.category-desc {{ color: rgba(255,255,255,0.6); font-size: 0.95rem; margin-bottom: 1.5rem; }}

/* Featured cards */
.featured-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }}
.featured-card {{
  background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 16px; padding: 1.25rem;
  transition: var(--transition);
}}
.featured-card:hover {{ border-color: var(--accent-cyan); transform: translateY(-4px); box-shadow: 0 10px 30px rgba(0,242,255,0.1); }}
.featured-name {{ font-weight: 700; margin-bottom: 0.5rem; }}
.featured-link {{ font-size: 0.9rem; margin-bottom: 0.5rem; }}
.featured-notes {{ color: rgba(255,255,255,0.65); font-size: 0.88rem; margin-bottom: 0.5rem; }}
.featured-monthly {{ font-size: 0.85rem; color: var(--accent-green); }}

/* Top 10 list */
.top-list {{ list-style: none; padding: 0; }}
.top-item {{
  display: grid; grid-template-columns: 40px 1fr auto auto; gap: 1rem; align-items: center;
  padding: 0.85rem 1rem; margin-bottom: 0.5rem; border-radius: 12px;
  background: var(--glass-bg); border: 1px solid var(--glass-border); transition: var(--transition);
}}
.top-item:hover {{ border-color: var(--accent-cyan); transform: translateX(4px); }}
.top-item.rank-1 {{ background: linear-gradient(90deg, rgba(0,242,255,0.08), transparent); border-color: rgba(0,242,255,0.3); }}
.top-item.rank-2 {{ background: linear-gradient(90deg, rgba(188,19,254,0.06), transparent); }}
.top-item.rank-3 {{ background: linear-gradient(90deg, rgba(74,222,128,0.05), transparent); }}
.rank {{
  font-family: var(--font-brand); font-size: 1.4rem; font-weight: 800; text-align: center;
  background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}}
.top-name {{ font-weight: 600; }}
.top-link {{ font-size: 0.85rem; }}
.top-monthly {{ font-size: 0.85rem; color: var(--accent-green); white-space: nowrap; }}

/* Bot table */
.table-wrap {{ overflow-x: auto; border-radius: 12px; border: 1px solid var(--glass-border); }}
.bot-table {{ width: 100%; border-collapse: collapse; min-width: 600px; }}
.bot-table th {{
  text-align: left; padding: 0.75rem 1rem; font-size: 0.85rem; font-weight: 600;
  color: rgba(255,255,255,0.6); background: rgba(255,255,255,0.03);
  border-bottom: 1px solid var(--glass-border); position: sticky; top: 0;
}}
.bot-table td {{ padding: 0.75rem 1rem; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.9rem; vertical-align: top; }}
.bot-table tr {{ transition: var(--transition); }}
.bot-table tbody tr:hover {{ background: rgba(0,242,255,0.04); }}
.bot-table tr:last-child td {{ border-bottom: none; }}
.col-name {{ font-weight: 600; white-space: nowrap; }}
.col-link {{ white-space: nowrap; }}
.col-monthly {{ white-space: nowrap; color: var(--accent-green); }}
.subsection-title {{ font-family: var(--font-brand); font-size: 1.15rem; font-weight: 600; margin: 1.5rem 0 0.75rem; color: var(--accent-purple); }}

/* Footer */
footer {{ padding: 3rem 0 2rem; border-top: 1px solid var(--glass-border); margin-top: 3rem; }}
.footer-content {{ display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap; }}
footer p {{ color: rgba(255,255,255,0.5); font-size: 0.85rem; }}
.footer-links {{ display: flex; gap: 1rem; }}
.footer-links a {{ color: rgba(255,255,255,0.5); }}
.footer-links a:hover {{ color: var(--accent-cyan); text-decoration: none; }}

/* Search filter: hide non-matching rows */
.bot-table tr.is-hidden {{ display: none; }}
.category-section.is-hidden {{ display: none; }}

/* Responsive */
@media (max-width: 768px) {{
  .hero {{ padding: 3rem 0 2rem; }}
  .top-item {{ grid-template-columns: 30px 1fr; gap: 0.5rem; }}
  .top-link, .top-monthly {{ grid-column: 2; }}
  .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
  nav ul {{ gap: 0.6rem; }}
  nav a {{ font-size: 0.8rem; }}
}}

@media (prefers-reduced-motion: reduce) {{
  html {{ scroll-behavior: auto; }}
  .blob-1, .blob-2, .blob-3 {{ animation: none; }}
  .featured-card:hover, .top-item:hover, .stat-card:hover, .btn:hover {{ transform: none; }}
}}
  </style>
</head>
<body>
  <div class="bg-blobs" aria-hidden="true">
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>
  </div>

  <header>
    <div class="container" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
      <a href="/" class="logo">电报机器人大全</a>
      <nav>
        <ul>
          <li><a href="#featured">精选</a></li>
          <li><a href="#top10">Top 10</a></li>
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
      <div class="hero-emergency">⚠️ t.me 域名已被注册局 serverHold，本页所有链接已替换为 telegram.me</div>
      <h1>中文 Telegram 机器人导航</h1>
      <p>精选 {total} 条活跃电报机器人，按 10 大场景分类组织，每条带真实月活数据，每周由 GitHub Actions 自动核验失效。</p>
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-num">{total}</div><div class="stat-label">收录 Bot</div></div>
        <div class="stat-card"><div class="stat-num">10</div><div class="stat-label">分类</div></div>
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
        <p>电报机器人大全 · 数据来自 Telegram 公开预览页 · 每周自动核验<br>构建于 {build_time}</p>
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
    OUT_FILE.write_text(build_html(data), encoding="utf-8")
    print(f"Site built: {OUT_FILE}")
    print(f"  - Total bots: {len(data.get('bots', []))}")
    print(f"  - Featured: {sum(1 for b in data.get('bots', []) if b.get('featured'))}")
    print(f"  - Output size: {OUT_FILE.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
