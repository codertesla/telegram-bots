# 贡献指南

欢迎为「电报机器人大全」贡献优质机器人、修复失效条目或改进基础设施。

本仓库的机器人列表不是手维护的 Markdown 表格，而是由 `data/bots.json` 驱动、脚本自动渲染到 README。这样能保证每条都有真实活跃度数据、每周自动核验失效，比纯手维护的列表更可信。贡献前请先阅读本指南。

---

## 快速贡献

### 方式一：提 Issue 推荐（最简单）
点击 [New Issue](https://github.com/codertesla/telegram-bots-cn/issues/new/choose)，选择「推荐机器人」模板，填入：

- 机器人名称
- 链接（**必须用 `https://telegram.me/xxx` 格式**，因 `t.me` 已被注册局 serverHold）
- 分类：搜索 / 群管 / 下载 / AI / RSS / 工具
- 一句话描述（核心功能 + 适用场景）
- 是否官方
- 开源仓库（如有）

### 方式二：报告失效机器人
在使用中发现列表里某机器人已失效，请提「机器人失效报告」Issue，打上 `dead-bot` 标签。维护者会核验后从 README 隐藏（仍保留在 `bots.json` 留痕）。

### 方式三：提 Pull Request
直接修改 `data/bots.json`，新增一条 bot 对象即可。**不要直接改 README 表格**——它会由 `scripts/render_readme.py` 自动生成，手改会被下次渲染覆盖。

---

## `data/bots.json` 字段说明

每条 bot 是 `bots` 数组的一个对象。字段分两组：

### 人工字段（贡献者填写，脚本不修改）
| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | 是 | username 去掉 `@`、全小写，作为主键，全局唯一 |
| `username` | 是 | 含 `@`，如 `@jiso` |
| `url` | 是 | `https://telegram.me/<username>`（不要用 t.me） |
| `category` | 是 | `search` / `group` / `download` / `ai` / `rss` / `tools` |
| `subsection` | 否 | 仅 `group` 类用：`verify` / `ads` / `stats` / `misc` |
| `featured` | 否 | `true` 进"精选必装"区，全区 ≤ 5 条 |
| `official` | 否 | 人工判断是否官方；抓取拿到的 Telegram 蓝勾优先级更高 |
| `notes` | 是 | 30-60 字中文，写清"核心功能 + 适用场景"，不带链接（链接由 url 自动渲染） |

### 抓取字段（由 `scripts/fetch_bots.py` 维护，贡献者勿改）
`fetch` 对象：`status`（`ok`/`dead`/`error`/`pending`）、`http_code`、`fetched_at`、`title`、`description`、`monthly_users`（int）、`type`（`bot`/`channel`/`group`/`unknown`）、`is_verified`、`photo_url`。

新增 bot 时 `fetch` 填 `{"status": "pending"}` 即可，下次抓取脚本会自动填入真实数据。

### 全局字段
`schema_version`（当前 `1`）、`last_fetched_at`（由脚本写）、`last_verified_label`（人类可读核验批次，写进 README 顶部"最近核验"）。

---

## 数据来源

`scripts/fetch_bots.py` 直接抓取 `https://telegram.me/<username>` 预览页（HTTP 200，服务端渲染，约 11 KB）。不使用 Telegram Bot API，无需任何 token。关键字段位置：

| 字段 | DOM | 示例 |
|---|---|---|
| 显示名 | `<div class="tgme_page_title">…</div>` | `极搜🔍中文搜索@JISO` |
| 自填简介 | `<div class="tgme_page_description">…</div>` | 含 `<br/>`、`<a>`，脚本会清洗成纯文本 |
| 活跃度 | `<div class="tgme_page_extra">…</div>`（页面里有两个该 class，只有含 `monthly users` / `subscribers` / `members` 的那个才是真实数据） | `299 956 monthly users` |
| 官方蓝勾 | `tgme_page_title` 内 `<i class="verified-icon">` | BotFather 有，jiso 无 |
| 头像 | `<img class="tgme_page_photo_image" src="…">` | `https://cdn5.telesco.pe/file/…jpg` |
| 类型推断 | 按 `extra` 文案：`monthly users`=bot / `subscribers`=channel / `members`=group | |
| 失效判定 | 无 `tgme_page_title`，或 HTTP 4xx | 标 `dead` |

---

## README 自动渲染

README 用 marker 包裹自动区块，其余散文由人工维护、**逐字符不动**。marker 成对、独占一行：

```
<!-- AUTO:last-verified:start --> … :end -->
<!-- AUTO:bots-featured:start --> … :end -->
<!-- AUTO:bots-category:search:start --> … :end -->
<!-- AUTO:bots-category:group:start --> … :end -->
<!-- AUTO:bots-category:download:start --> … :end -->
<!-- AUTO:bots-category:ai:start --> … :end -->
<!-- AUTO:bots-category:rss:start --> … :end -->
<!-- AUTO:bots-category:tools:start --> … :end -->
```

`scripts/render_readme.py` 读 `bots.json` 重写 marker 区块。渲染规则：
- 精选区：表格列 `名称 | 链接 | 一句话用途 | 月活`
- 月活显示：bot `约 30 万/月`、channel `30 万 订阅`、group `30 万 成员`；≥1万用"万"、≥1亿用"亿"
- dead 条目仍显示，加 `❗已失效（YYYY-MM）`
- 官方蓝勾或人工 official 在显示名后加 `✓`

---

## 本地开发

### 依赖
```bash
pip install -r scripts/requirements.txt
```
仅依赖 `requests` + `beautifulsoup4`。

### 工作流
```bash
# 1. 改 data/bots.json（新增/编辑 bot 条目）

# 2. 抓取最新元数据（礼貌限流 ≥2s，4xx 自动标 dead）
python scripts/fetch_bots.py

# 3. 重新渲染 README
python scripts/render_readme.py

# 4. 全量自检（退出码 0 才可提交）
python scripts/validate.py
```

`validate.py` 含 4 个子项：
- `--check seed`：bots.json 人工字段完整、id 唯一、category 合法、featured ≤ 5
- `--check readme`：marker 成对、每条 bot 都被渲染、无残留手写链接
- `--check links`：所有 `telegram.me/xxx` 链接与 json.url 一致
- `--check dead`：dead 条目均已附失效标记

无参数 = 跑全部。

### 抓取脚本选项
```bash
python scripts/fetch_bots.py                 # 抓 pending 与过期条目
python scripts/fetch_bots.py --id jiso        # 只抓某条
python scripts/fetch_bots.py --force          # 忽略缓存全部重抓
python scripts/fetch_bots.py --dry-run        # 只打印不写文件
python scripts/fetch_bots.py --sleep 3        # 调整限流（最小 1s 强制下限）
```

幂等保证：新抓结果与旧值完全一致时不刷新 `fetched_at`，避免制造无意义 diff。

---

## CI 自动刷新

`.github/workflows/refresh.yml` 每周一 03:00 UTC 自动跑：
1. `fetch_bots.py` 抓最新元数据
2. `render_readme.py` 重写 README
3. `validate.py` 自检
4. 通过则 commit+push，失败则自动开 Issue（`auto-refresh-failed` 标签）

手动触发可在仓库 Actions 页选 "Bot Data Auto-Refresh" → "Run workflow"。

---

## 收录原则

- **实用**：对中文用户有真实使用价值
- **稳定**：优先长期运营、有月活数据佐证的
- **干净**：不收机场、流量卡、涨粉、博彩拉新、色情导航等灰产类
- **去重**：精选区 ≤ 5 条，分类区按 username 去重
- **失效即标**：dead 不删，加 `❗已失效`，连续 3 次 CI 仍 dead 则从 README 隐藏
- **AI 类慎收**：AI 机器人迭代太快，`category=ai` 可用 `url=null` 占位（只渲染散文引导，不固定具体账号）

---

## 许可证

本仓库所有内容（README、data、scripts、本文档）采用 [MIT License](./LICENSE)。贡献内容同协议。

---

## 致谢

本仓库参考了社区优秀列表（itgoyo/TelegramBot、AZeC4/TelegramBot 等）在选品上的积累，并在结构、活跃度核验、自动维护上做了差异化。

**觉得有用请点个 Star ⭐，让更多人看到这个列表。**