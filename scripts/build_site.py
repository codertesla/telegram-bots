#!/usr/bin/env python3
"""
build_site.py - 把 data/bots.json 烘焙为 docs/index.html 静态站点。

设计系统适配自 codertesla.github.io 的 Editorial Dark 风：
- 深色背景 (#0a0a0a) + 金色强调色 (#e8b04d)
- Space Grotesk 标题 / Inter 正文
- 行式列表替代宽表格：名称与 @用户名合并为一列，整行可点

信息架构（自上而下）：
1. 头部：品牌 + 精选/Top10 锚点 + GitHub
2. 吸顶工具栏：实时搜索 + 分类筛选 chips（带条数）
3. Hero：标题、导语、内联数据摘要、CTA
4. 精选必装：5 张等宽卡片，宽屏一行排满
5. 月活 Top 10：双列紧凑列表
6. 分类区：统一行布局（名称+用户名 / 功能说明 / 月活）

数据全部预渲染进 HTML，无需运行时 fetch；输出只依赖 bots.json
（页脚时间取 last_fetched_at），数据不变则 docs/index.html 不变。
fetch.dead_streak >= HIDE_AFTER 的条目隐藏；not_bot 条目加 ⚠️ 标记。
"""
import html
import json
import re
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

# 吸顶工具栏的短标签
CATEGORY_SHORT = {
    "official": "官方",
    "search": "搜索",
    "crypto": "加密",
    "group": "群管",
    "download": "下载",
    "ai": "AI",
    "translate": "翻译",
    "checkin": "签到",
    "channel": "频道",
    "game": "游戏",
    "tools": "工具",
}

CATEGORY_ORDER = ["official", "search", "crypto", "group", "download", "ai", "translate", "checkin", "channel", "game", "tools"]

HIDE_AFTER = 3  # keep in sync with scripts/fetch_bots.py

NOT_BOT_LABELS = {
    "channel": "⚠️已变为频道（非 Bot）",
    "group": "⚠️已变为群组（非 Bot）",
    "user": "⚠️个人账号（非 Bot）",
}

SUBSECTION_TITLES = {
    "verify": "进群验证",
    "ads": "广告拦截",
    "stats": "活跃统计",
    "misc": "秩序维护",
}


def esc(value):
    """HTML 转义（含引号），用于文本与属性值。"""
    return html.escape(str(value), quote=True)


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


def format_num(n):
    if n is None:
        return "—"
    if n >= 100_000_000:
        return f"{n / 100_000_000:.1f} 亿"
    if n >= 10_000:
        return f"{n / 10_000:.1f} 万"
    return str(n)


def metric_html(bot):
    """月活列：正常 / 非 Bot / 已失效三种呈现。"""
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
        return f'{badge}<span class="metric-sub">{format_num(users)}{unit}</span>'
    if not users:
        return '<span class="muted">—</span>'
    typ = fetch.get("type") or "bot"
    unit = {"bot": "/月", "channel": " 订阅", "group": " 成员"}.get(typ, "/月")
    return f'<strong>{format_num(users)}</strong><span class="metric-sub">{unit}</span>'


def clean_display_title(raw):
    s = re.sub(r"[🔍🤖🐴🇺🇦⚡️🎲🐰\ufe0f]+", "", raw)
    s = re.sub(r"\s*Powered by @[A-Za-z0-9_]+", "", s, flags=re.I)
    s = re.sub(r"\s*@[A-Za-z0-9_]+\s*$", "", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s


def display_name(bot):
    fetch = bot.get("fetch", {}) or {}
    raw_title = fetch.get("title") or bot.get("username", "").lstrip("@")
    title = clean_display_title(str(raw_title)) or str(raw_title).strip()
    title = esc(title)
    if fetch.get("is_verified") or bot.get("official"):
        title = f'{title} <span class="verified" title="已认证">✓</span>'
    return title


def handle(bot):
    """@用户名（纯文本，父元素是链接，避免嵌套 <a>）。"""
    username = bot.get("username", "")
    if not username:
        return '<span class="handle muted">—</span>'
    return f'<span class="handle">{esc(username)}</span>'


def notes_field(bot):
    return esc(bot.get("notes", ""))


def search_blob(bot):
    """行内检索文本：名称、用户名、说明、分类名全部小写预拼好，客户端无需再算。"""
    parts = [
        bot.get("username", ""),
        bot.get("notes", ""),
        clean_display_title(str((bot.get("fetch", {}) or {}).get("title") or "")),
        CATEGORY_TITLES.get(bot.get("category"), ("", ""))[0],
        SUBSECTION_TITLES.get(bot.get("subsection") or "", ""),
    ]
    return esc(" ".join(p for p in parts if p).lower())


def render_bot_row(bot):
    cat = bot.get("category", "")
    url = bot.get("url")
    attrs = f'data-category="{esc(cat)}" data-search="{search_blob(bot)}"'
    def body():
        return f"""            <span class="bot-id">
              <span class="bot-name">{display_name(bot)}</span>
              {handle(bot)}
            </span>
            <span class="bot-notes">{notes_field(bot)}</span>
            <span class="bot-metric">{metric_html(bot)}</span>
            <span class="bot-go" aria-hidden="true">↗</span>"""

    if url:
        return f"""        <li>
          <a class="bot-row" href="{esc(url)}" target="_blank" rel="noopener" {attrs}>
{body()}
          </a>
        </li>"""
    return f"""        <li>
          <div class="bot-row is-static" {attrs}>
            <span class="bot-id">
              <span class="bot-name">{display_name(bot)}</span>
              {handle(bot)}
            </span>
            <span class="bot-notes">{notes_field(bot)}</span>
            <span class="bot-metric">{metric_html(bot)}</span>
          </div>
        </li>"""


def render_bot_list(bots):
    if not bots:
        return '      <p class="muted">暂无收录。</p>'
    rows = "\n".join(render_bot_row(b) for b in bots)
    return f"""      <ul class="bot-list">
{rows}
      </ul>"""


def render_group_section(bots):
    """群管类按 subsection 分组渲染 4 个小列表；组内按月活降序。"""
    parts = []
    for sub_key in ["verify", "ads", "stats", "misc"]:
        sub_bots = sort_by_monthly([b for b in bots if (b.get("subsection") or "misc") == sub_key])
        if not sub_bots:
            continue
        title = SUBSECTION_TITLES.get(sub_key, sub_key)
        parts.append(f'      <h3 class="sub-title">{title}<span class="sub-count">{len(sub_bots)}</span></h3>')
        parts.append(render_bot_list(sub_bots))
    return "\n".join(parts)


def render_category_section(cat, bots):
    title, desc = CATEGORY_TITLES.get(cat, (cat, ""))
    if cat == "group":
        body = render_group_section(bots)
    else:
        body = render_bot_list(sort_by_monthly(bots))
    return f"""    <section class="section" id="cat-{cat}" data-category="{cat}">
      <div class="section-head">
        <h2 class="section-title">{title}</h2>
        <span class="section-count">{len(bots)} 个</span>
      </div>
      <p class="section-desc">{desc}</p>
{body}
    </section>"""


def render_chips(by_cat):
    total = sum(len(v) for v in by_cat.values())
    chips = [f'        <a class="chip is-active" href="#top" data-filter="all">全部<span class="n">{total}</span></a>']
    for cat in CATEGORY_ORDER:
        bots = by_cat.get(cat) or []
        if not bots:
            continue
        chips.append(
            f'        <a class="chip" href="#cat-{cat}" data-filter="{cat}">{CATEGORY_SHORT.get(cat, cat)}'
            f'<span class="n">{len(bots)}</span></a>'
        )
    return "\n".join(chips)


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
        url = b.get("url") or "#"
        items.append(f"""        <li>
          <a class="rank-row rank-{i}" href="{esc(url)}" target="_blank" rel="noopener"
             data-category="{esc(b.get('category', ''))}" data-search="{search_blob(b)}">
            <span class="rank">{i}</span>
            <span class="rank-name">{display_name(b)}</span>
            {handle(b)}
            <span class="rank-metric">{metric_html(b)}</span>
          </a>
        </li>""")
    return f"""    <section class="section" id="top10">
      <div class="section-head">
        <h2 class="section-title">月活 Top 10</h2>
        <span class="section-count">按公开月活</span>
      </div>
      <p class="section-desc">本列表中第三方 bot 按 Telegram 公开月活数据排名，每周自动核验；官方账号月活量级不同，单列在官方分类。</p>
      <ol class="rank-list">
{chr(10).join(items)}
      </ol>
    </section>"""


def render_featured(featured_bots):
    if not featured_bots:
        return ""
    cards = []
    for b in sort_by_monthly(featured_bots):
        url = b.get("url") or "#"
        cards.append(f"""        <li>
          <a class="fcard" href="{esc(url)}" target="_blank" rel="noopener"
             data-category="{esc(b.get('category', ''))}" data-search="{search_blob(b)}">
            <span class="fcard-name">{display_name(b)}</span>
            {handle(b)}
            <span class="fcard-notes">{notes_field(b)}</span>
            <span class="fcard-metric">{metric_html(b)}</span>
          </a>
        </li>""")
    return f"""    <section class="section" id="featured">
      <div class="section-head">
        <h2 class="section-title">精选必装</h2>
        <span class="section-count">{len(featured_bots)} 个场景</span>
      </div>
      <p class="section-desc">覆盖最高频使用场景的入口（官方 / 搜索 / 群管 / 下载 / 娱乐），每个场景只放该分类月活最高、确认在运营的一个。</p>
      <ul class="featured-grid">
{chr(10).join(cards)}
      </ul>
    </section>"""


CSS = """
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#0a0a0a;--bg-soft:#101010;--card:#161616;--card-hover:#1c1c1c;
  --text:#ededed;--muted:#9a9a9a;--faint:#6e6e6e;
  --border:rgba(255,255,255,.08);--border-strong:rgba(255,255,255,.15);
  --accent:#e8b04d;--accent-hover:#f5d68a;--accent-soft:rgba(232,176,77,.12);
  --danger:#f87171;--danger-soft:rgba(239,68,68,.13);
  --font-heading:'Space Grotesk','Inter',-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;
  --font-main:'Inter',-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;
  --ease:cubic-bezier(.2,.7,.3,1);--radius:14px;
}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{background:var(--bg);color:var(--text);font-family:var(--font-main);line-height:1.6;
  -webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:var(--accent);text-decoration:none;transition:color .18s var(--ease),border-color .18s var(--ease),background-color .18s var(--ease)}
a:hover{color:var(--accent-hover)}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:6px}
.container{width:100%;max-width:1160px;margin:0 auto;padding:0 1.25rem}
.muted{color:var(--muted)}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
[hidden]{display:none !important}

/* ---------- Header ---------- */
.site-header{position:relative;border-bottom:1px solid var(--border)}
.site-header::after{content:'';position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(70% 130% at 50% 0%,rgba(232,176,77,.055),transparent 72%)}
.header-inner{display:flex;align-items:center;justify-content:space-between;gap:1rem;min-height:60px}
.brand{display:inline-flex;align-items:center;gap:.55rem;font-family:var(--font-heading);
  font-weight:700;font-size:1rem;letter-spacing:-.01em;color:var(--text)}
.brand:hover{color:var(--text)}
.brand-dot{width:7px;height:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 10px rgba(232,176,77,.85)}
.header-nav{display:flex;align-items:center;gap:1.15rem;font-size:.85rem}
.header-nav a{color:var(--muted)}
.header-nav a:hover{color:var(--text)}

/* ---------- Sticky toolbar ---------- */
.toolbar{position:sticky;top:0;z-index:60;border-bottom:1px solid var(--border);
  background:rgba(10,10,10,.82);backdrop-filter:saturate(150%) blur(14px);
  -webkit-backdrop-filter:saturate(150%) blur(14px)}
.toolbar-inner{display:flex;align-items:center;gap:.7rem;padding:.55rem 1.25rem;
  max-width:1160px;margin:0 auto}
.search-field{position:relative;flex:0 1 250px;min-width:132px}
.search-field svg{position:absolute;left:.7rem;top:50%;transform:translateY(-50%);
  width:14px;height:14px;stroke:var(--faint);fill:none;stroke-width:2;stroke-linecap:round;pointer-events:none}
#search{width:100%;padding:.46rem .8rem .46rem 2rem;font-size:.85rem;font-family:var(--font-main);
  color:var(--text);background:var(--card);border:1px solid var(--border);border-radius:999px;
  outline:none;transition:border-color .18s var(--ease),background-color .18s var(--ease);
  -webkit-appearance:none;appearance:none}
#search:focus{border-color:var(--accent);background:var(--bg-soft)}
#search::placeholder{color:var(--faint)}
#search::-webkit-search-cancel-button{-webkit-appearance:none;appearance:none}
.chips{display:flex;align-items:center;gap:.35rem;overflow-x:auto;scrollbar-width:none;flex:1 1 auto;padding:.1rem 0}
.chips::-webkit-scrollbar{display:none}
.chip{white-space:nowrap;padding:.28rem .62rem;border:1px solid var(--border);border-radius:999px;
  font-size:.8rem;color:var(--muted);transition:all .18s var(--ease)}
.chip:hover{color:var(--text);border-color:var(--border-strong);text-decoration:none}
.chip.is-active{background:var(--accent);border-color:var(--accent);color:#0a0a0a;font-weight:600}
.chip .n{margin-left:.28rem;font-size:.74rem;font-variant-numeric:tabular-nums;opacity:.5}
.chip.is-active .n{opacity:.62}
.count{flex:0 0 auto;font-size:.78rem;color:var(--faint);font-variant-numeric:tabular-nums;white-space:nowrap}

/* ---------- Hero ---------- */
.hero{padding:3.4rem 0 1.2rem;scroll-margin-top:72px}
.eyebrow{font-family:var(--font-heading);font-size:.72rem;letter-spacing:.16em;
  text-transform:uppercase;color:var(--accent);margin-bottom:.85rem}
.hero h1{font-family:var(--font-heading);font-size:clamp(1.75rem,4.4vw,3rem);font-weight:700;
  line-height:1.16;letter-spacing:-.025em;margin-bottom:.85rem;text-wrap:balance}
.lede{color:var(--muted);font-size:.98rem;max-width:62ch;margin-bottom:1.5rem}
.hero-meta{display:flex;flex-wrap:wrap;align-items:center;gap:.55rem .9rem;
  font-size:.82rem;color:var(--faint);margin-bottom:1.6rem}
.hero-meta span{display:inline-flex;align-items:baseline;gap:.35rem}
.hero-meta strong{font-family:var(--font-heading);font-size:1.02rem;font-weight:600;color:var(--text);
  font-variant-numeric:tabular-nums}
.hero-meta .sep{width:1px;height:13px;background:var(--border-strong);display:inline-block}
.hero-actions{display:flex;gap:.55rem;flex-wrap:wrap}
.btn{display:inline-block;padding:.52rem 1.05rem;border-radius:8px;font-size:.87rem;font-weight:600;
  background:var(--accent);border:1px solid var(--accent);color:#0a0a0a;
  transition:all .18s var(--ease)}
.btn:hover{background:var(--accent-hover);border-color:var(--accent-hover);color:#0a0a0a;text-decoration:none}
.btn-ghost{background:transparent;border-color:var(--border-strong);color:var(--text)}
.btn-ghost:hover{border-color:var(--accent);color:var(--accent);background:transparent}

/* ---------- Sections ---------- */
.section{padding:2.4rem 0 0;scroll-margin-top:72px}
.section-head{display:flex;align-items:baseline;justify-content:space-between;gap:1rem;margin-bottom:.35rem}
.section-title{font-family:var(--font-heading);font-size:1.32rem;font-weight:600;letter-spacing:-.01em;
  display:flex;align-items:center;gap:.6rem}
.section-title::before{content:'';width:3px;height:1.02em;background:var(--accent);border-radius:2px}
.section-count{font-size:.78rem;color:var(--faint);font-variant-numeric:tabular-nums;white-space:nowrap}
.section-desc{color:var(--muted);font-size:.88rem;margin-bottom:1.15rem;max-width:82ch}
.sub-title{font-family:var(--font-heading);font-size:.95rem;font-weight:600;color:var(--text);
  margin:1.6rem 0 .5rem;padding-top:.9rem;border-top:1px solid var(--border);
  display:flex;align-items:center;gap:.5rem;letter-spacing:.01em}
.sub-title:first-of-type{margin-top:.8rem;padding-top:0;border-top:0}
.sub-title::before{content:'';width:5px;height:5px;border-radius:50%;background:var(--accent);opacity:.8}
.sub-count{font-size:.74rem;color:var(--faint);font-weight:500;font-variant-numeric:tabular-nums}

/* ---------- Featured ---------- */
.featured-grid{list-style:none;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.7rem}
.fcard{display:flex;flex-direction:column;gap:.3rem;height:100%;padding:1rem .95rem;
  background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  color:var(--text);transition:all .2s var(--ease)}
.fcard:hover{border-color:rgba(232,176,77,.42);background:var(--card-hover);
  transform:translateY(-2px);text-decoration:none;color:var(--text)}
.fcard-name{font-family:var(--font-heading);font-weight:600;font-size:.95rem;line-height:1.3;letter-spacing:-.01em}
.fcard-name .verified{color:var(--accent);font-weight:700;font-size:.85em}
.fcard .handle{font-size:.75rem;color:var(--accent);opacity:.9}
.fcard-notes{font-size:.8rem;color:var(--muted);line-height:1.55;flex:1;margin-top:.35rem}
.fcard-metric{font-size:.78rem;color:var(--faint);padding-top:.55rem;margin-top:.35rem;
  border-top:1px solid var(--border);font-variant-numeric:tabular-nums}
.fcard-metric strong{color:var(--text);font-weight:600}

/* ---------- Rank list ---------- */
.rank-list{list-style:none;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.45rem}
.rank-row{display:grid;grid-template-columns:22px minmax(0,1fr) auto auto;align-items:center;
  gap:.6rem;padding:.55rem .8rem;border:1px solid var(--border);border-radius:10px;
  background:var(--card);color:var(--text);transition:all .18s var(--ease)}
.rank-row:hover{border-color:rgba(232,176,77,.4);background:var(--card-hover);text-decoration:none;color:var(--text)}
.rank{font-family:var(--font-heading);font-size:.85rem;font-weight:700;text-align:center;
  color:var(--faint);font-variant-numeric:tabular-nums}
.rank-1 .rank{color:var(--accent);font-size:.95rem}
.rank-2 .rank{color:var(--accent);opacity:.8}
.rank-3 .rank{color:var(--accent);opacity:.62}
.rank-name{font-weight:600;font-size:.88rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rank-name .verified{color:var(--accent);font-size:.85em}
.rank-row .handle{font-size:.75rem;color:var(--faint);white-space:nowrap}
.rank-metric{font-size:.8rem;text-align:right;white-space:nowrap;color:var(--muted);font-variant-numeric:tabular-nums}
.rank-metric strong{color:var(--text);font-weight:600}
.metric-sub{color:var(--faint);font-weight:400}

/* ---------- Bot rows ---------- */
.bot-list{list-style:none}
.bot-list li + li .bot-row{box-shadow:inset 0 1px 0 rgba(255,255,255,.065)}
.bot-row{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1.85fr) minmax(84px,auto) 14px;
  align-items:center;gap:1rem;padding:.62rem .8rem;border-radius:10px;color:var(--text);
  transition:background-color .16s var(--ease),box-shadow .16s var(--ease)}
.bot-row:hover{background:var(--card);text-decoration:none;color:var(--text);
  box-shadow:inset 3px 0 0 var(--accent),inset 0 0 0 1px var(--border)}
.bot-id{display:flex;flex-direction:column;gap:.05rem;min-width:0}
.bot-name{font-weight:600;font-size:.9rem;line-height:1.4;overflow-wrap:anywhere}
.bot-name .verified{color:var(--accent);font-size:.85em;font-weight:700}
.handle{font-size:.75rem;color:var(--faint);overflow-wrap:anywhere}
.bot-notes{font-size:.84rem;color:var(--muted);line-height:1.5;min-width:0;overflow-wrap:anywhere}
.bot-metric{font-size:.82rem;text-align:right;white-space:nowrap;color:var(--muted);font-variant-numeric:tabular-nums}
.bot-metric strong{color:var(--text);font-weight:600}
.bot-go{font-size:.78rem;color:var(--faint);opacity:0;transition:all .18s var(--ease)}
.bot-row:hover .bot-go{opacity:1;color:var(--accent);transform:translate(2px,-2px)}
.badge{display:inline-block;font-size:.74rem;padding:1px 7px;border-radius:6px;line-height:1.6}
.badge-dead{background:var(--danger-soft);color:var(--danger);border:1px solid rgba(239,68,68,.28);
  display:block;margin-bottom:2px;text-align:left}
.bot-metric .badge + .metric-sub{display:block;margin-top:1px}

/* ---------- Empty state ---------- */
.empty{padding:3.5rem 0;text-align:center}
.empty p:first-child{font-family:var(--font-heading);font-size:1.05rem;margin-bottom:.4rem}
.empty p + p{font-size:.86rem}

/* ---------- Footer ---------- */
.site-footer{border-top:1px solid var(--border);margin-top:3.5rem;padding:2.2rem 0 2.6rem}
.footer-inner{display:flex;justify-content:space-between;align-items:flex-start;gap:1.5rem;flex-wrap:wrap}
.footer-inner p{color:var(--faint);font-size:.8rem;line-height:1.7}
.footer-links{display:flex;gap:1.1rem;font-size:.8rem}
.footer-links a{color:var(--muted)}
.footer-links a:hover{color:var(--text)}

/* ---------- Back to top ---------- */
.to-top{position:fixed;right:1.1rem;bottom:1.1rem;z-index:70;width:38px;height:38px;
  display:grid;place-items:center;border-radius:50%;background:var(--card);
  border:1px solid var(--border-strong);color:var(--muted);font-size:.9rem;cursor:pointer;
  opacity:0;pointer-events:none;transition:all .2s var(--ease)}
.to-top.is-visible{opacity:1;pointer-events:auto}
.to-top:hover{color:var(--accent);border-color:var(--accent);background:var(--card-hover)}

/* ---------- Responsive ---------- */
@media (max-width:1000px){
  .featured-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  /* 5 张卡片在双列下会剩一张，让它独占整行 */
  .featured-grid li:last-child:nth-child(odd){grid-column:1 / -1}
}
@media (max-width:860px){
  .bot-row{grid-template-columns:minmax(0,1fr) minmax(0,1.4fr) minmax(76px,auto)}
  .bot-go{display:none}
  .header-nav{display:none}
  /* 工具栏改为两行：搜索独占一行，分类 chips 另起一行横向滚动 */
  .toolbar-inner{flex-wrap:wrap;gap:.45rem;padding:.5rem 1rem}
  .search-field{flex:1 1 100%;min-width:0}
  .chips{flex:1 1 100%;order:3;
    -webkit-mask-image:linear-gradient(to right,#000 90%,transparent 100%);
    mask-image:linear-gradient(to right,#000 90%,transparent 100%)}
  .count{display:none}
}
@media (max-width:720px){
  .hero{padding:2.4rem 0 1rem}
  .rank-list{grid-template-columns:minmax(0,1fr)}
  .bot-row{grid-template-columns:minmax(0,1fr) auto;gap:.25rem .7rem;
    padding:.7rem;align-items:start}
  .bot-id{grid-column:1;grid-row:1}
  .bot-metric{grid-column:2;grid-row:1;font-size:.78rem}
  .bot-notes{grid-column:1 / -1;grid-row:2;font-size:.8rem}
  .section{scroll-margin-top:116px}
}
@media (max-width:520px){
  .featured-grid{grid-template-columns:minmax(0,1fr)}
  .hero-meta{font-size:.78rem}
  .section-title{font-size:1.15rem}
}
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *{transition:none !important}
  .fcard:hover{transform:none}
}
"""

JS = """
(function () {
  var input = document.getElementById('search');
  var rows = Array.prototype.slice.call(document.querySelectorAll('.bot-row'));
  var cards = Array.prototype.slice.call(document.querySelectorAll('.fcard'));
  var rankRows = Array.prototype.slice.call(document.querySelectorAll('.rank-row'));
  var sections = Array.prototype.slice.call(document.querySelectorAll('.section[data-category]'));
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var counter = document.getElementById('count');
  var empty = document.getElementById('empty');
  var toTop = document.getElementById('toTop');
  var featuredSec = document.getElementById('featured');
  var top10Sec = document.getElementById('top10');
  var total = rows.length;
  var activeCat = 'all';

  function li(el) { return el.parentElement; }

  function match(el) {
    var okCat = activeCat === 'all' || el.getAttribute('data-category') === activeCat;
    var okQ = !query || (el.getAttribute('data-search') || '').indexOf(query) !== -1;
    return okCat && okQ;
  }

  function anyVisible(list) {
    return list.some(function (el) { return !li(el).hidden; });
  }

  var query = '';

  function apply() {
    var shown = 0;

    rows.forEach(function (el) {
      var ok = match(el);
      li(el).hidden = !ok;
      if (ok) { shown++; }
    });

    cards.forEach(function (el) { li(el).hidden = !match(el); });
    rankRows.forEach(function (el) { li(el).hidden = !match(el); });

    sections.forEach(function (sec) {
      sec.hidden = !anyVisible(Array.prototype.slice.call(sec.querySelectorAll('.bot-row')));
    });

    if (featuredSec) {
      featuredSec.hidden = !anyVisible(Array.prototype.slice.call(featuredSec.querySelectorAll('.fcard')));
    }
    if (top10Sec) {
      top10Sec.hidden = !anyVisible(Array.prototype.slice.call(top10Sec.querySelectorAll('.rank-row')));
    }

    if (counter) {
      var pool = rows.filter(function (el) {
        return activeCat === 'all' || el.getAttribute('data-category') === activeCat;
      }).length;
      counter.textContent = shown === pool ? pool + ' 个机器人' : '匹配 ' + shown + ' / ' + pool;
    }
    empty.hidden = shown !== 0;
  }

  function setCat(cat) {
    activeCat = cat;
    chips.forEach(function (c) {
      c.classList.toggle('is-active', c.getAttribute('data-filter') === cat);
    });
    apply();
  }

  chips.forEach(function (chip) {
    chip.addEventListener('click', function (e) {
      e.preventDefault();
      setCat(chip.getAttribute('data-filter'));
      if (activeCat !== 'all') {
        var target = document.getElementById('cat-' + activeCat);
        if (target && !target.hidden) {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      } else {
        var top = document.getElementById('top');
        if (top) { window.scrollTo({ top: 0, behavior: 'smooth' }); }
      }
      if (history.replaceState) {
        history.replaceState(null, '', activeCat === 'all'
          ? location.pathname + location.search
          : '#cat-' + activeCat);
      }
    });
  });

  input.addEventListener('input', function () {
    query = (input.value || '').trim().toLowerCase();
    apply();
  });

  input.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      input.value = '';
      query = '';
      setCat('all');
      input.blur();
    }
  });

  document.addEventListener('keydown', function (e) {
    var tag = (document.activeElement && document.activeElement.tagName) || '';
    if (e.key === '/' && tag !== 'INPUT' && tag !== 'TEXTAREA') {
      e.preventDefault();
      input.focus();
    }
  });

  if (toTop) {
    window.addEventListener('scroll', function () {
      toTop.classList.toggle('is-visible', window.scrollY > 600);
    }, { passive: true });
    toTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  apply();
})();
"""


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
    live_cats = [cat for cat in CATEGORY_ORDER if by_cat.get(cat)]
    cat_count = len(live_cats)

    featured_html = render_featured(featured)
    top10_html = render_top10(bots)
    cat_sections = "\n".join(
        render_category_section(cat, by_cat.get(cat, [])) for cat in live_cats
    )
    chips_html = render_chips(by_cat)

    verified_time = format_verified_time(data.get("last_fetched_at"))
    cat_names = "、".join(CATEGORY_TITLES[cat][0] for cat in live_cats)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>电报机器人大全 | 精选实用 Telegram Bot 推荐（{last_label}）</title>
  <meta name="description" content="中文 Telegram 机器人导航列表：{total} 条精选 bot，带真实月活数据，每周自动核验失效。覆盖{cat_names}等 {cat_count} 大分类。">
  <meta name="keywords" content="电报机器人,Telegram 机器人,TG 机器人,Telegram Bot 推荐,群管理机器人,中文 TG Bot">
  <meta name="theme-color" content="#0a0a0a">
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
  <style>{CSS}</style>
</head>
<body id="top">
  <header class="site-header">
    <div class="container header-inner">
      <a href="/" class="brand"><span class="brand-dot" aria-hidden="true"></span>电报机器人大全</a>
      <nav class="header-nav" aria-label="页面导航">
        <a href="#featured">精选</a>
        <a href="#top10">Top 10</a>
        <a href="https://github.com/codertesla/telegram-bots" target="_blank" rel="noopener">GitHub ↗</a>
      </nav>
    </div>
  </header>

  <div class="toolbar">
    <div class="toolbar-inner">
      <div class="search-field">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><path d="M20 20l-3.6-3.6"></path></svg>
        <label class="sr-only" for="search">搜索机器人</label>
        <input type="search" id="search" autocomplete="off" placeholder="搜索名称、关键词或用户名">
      </div>
      <div class="chips" role="group" aria-label="分类筛选">
{chips_html}
      </div>
      <span class="count" id="count">{total} 个机器人</span>
    </div>
  </div>

  <main class="container">
    <section class="hero">
      <p class="eyebrow">Telegram · 中文精选</p>
      <h1>中文 Telegram 机器人导航</h1>
      <p class="lede">精选 {total} 条活跃电报机器人，按 {cat_count} 大场景分类组织，每条带真实月活数据，每周由 GitHub Actions 自动核验失效。</p>
      <div class="hero-meta">
        <span><strong>{total}</strong>收录</span>
        <i class="sep" aria-hidden="true"></i>
        <span><strong>{cat_count}</strong>分类</span>
        <i class="sep" aria-hidden="true"></i>
        <span><strong>{ok_count}</strong>活跃</span>
        <i class="sep" aria-hidden="true"></i>
        <span><strong>{last_label}</strong>核验</span>
      </div>
      <div class="hero-actions">
        <a href="#featured" class="btn">浏览精选</a>
        <a href="https://github.com/codertesla/telegram-bots" target="_blank" rel="noopener" class="btn btn-ghost">查看 GitHub</a>
      </div>
    </section>

    <div class="empty" id="empty" hidden>
      <p>没有找到匹配的机器人</p>
      <p class="muted">换个更短的关键词，或点顶部「全部」查看所有分类</p>
    </div>

{featured_html}

{top10_html}

{cat_sections}
  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <p>电报机器人大全 · 数据来自 Telegram 公开预览页 · 每周自动核验<br>数据核验于 {verified_time}</p>
      <div class="footer-links">
        <a href="https://github.com/codertesla/telegram-bots" target="_blank" rel="noopener">GitHub</a>
        <a href="https://github.com/codertesla/telegram-bots/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener">贡献指南</a>
        <a href="https://github.com/codertesla/telegram-bots/issues/new/choose" target="_blank" rel="noopener">推荐 Bot</a>
      </div>
    </div>
  </footer>

  <button class="to-top" id="toTop" type="button" aria-label="回到顶部">↑</button>

  <script>{JS}</script>
</body>
</html>"""


def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    html_out = build_html(data)
    if OUT_FILE.exists() and OUT_FILE.read_text(encoding="utf-8") == html_out:
        print(f"Site unchanged: {OUT_FILE}")
    else:
        OUT_FILE.write_text(html_out, encoding="utf-8")
        print(f"Site built: {OUT_FILE}")
    print(f"  - Total bots shown: {sum(1 for b in data.get('bots', []) if not is_hidden(b))}")
    print(f"  - Featured: {sum(1 for b in data.get('bots', []) if b.get('featured'))}")
    print(f"  - Output size: {OUT_FILE.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
