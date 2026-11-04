# 贡献指南

欢迎为「电报机器人大全」贡献优质机器人、修复失效条目或改进基础设施。

本仓库的机器人列表不是手维护的 Markdown 表格，而是由 `data/bots.json` 驱动、脚本自动渲染到 README。活跃度数据来自 Telegram 公开预览页并每周复核，比纯手维护的列表更可信。注意脚本只核验**预览页存在性与公开月活**，不检测 `/start` 是否真的响应。贡献前请先阅读本指南。

---

## 快速贡献

### 方式一：提 Issue 推荐（最简单）
点击 [New Issue](https://github.com/codertesla/telegram-bots/issues/new/choose)，选择「推荐机器人」模板，填入：

- 机器人名称
- 链接（**必须用 `https://t.me/xxx` 格式**；允许追加 `?start=<邀请码>` 深链参数。唯一例外是 Crypto Pay 的转账深链 `https://t.me/send?start=...`，路径与 username 不同；抓取脚本始终按 `username` 请求 `t.me/<username>` 预览页，不受 url 参数影响）
- 分类：官方 / 搜索 / 加密交易 / 群管 / 下载 / AI / 翻译 / 签到 / 频道推送 / 游戏 / 工具（官方指 Telegram 自家账号与频道）
- 一句话描述（核心功能 + 适用场景）
- 是否官方
- 开源仓库（如有）

### 方式二：报告失效机器人
在使用中发现列表里某机器人已失效，请提「机器人失效报告」Issue，打上 `dead-bot` 标签。维护者核验确认后会将该条从 `bots.json` 中直接移除，列表只保留在运营的机器人。

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
| `url` | 是 | `https://t.me/<username>`，可带 `?start=` 邀请参数；`t.me/send` 为 Crypto Pay 转账深链特例 |
| `category` | 是 | `official` / `search` / `group` / `download` / `ai` / `tools` / `translate` / `checkin` / `channel` / `game` |
| `subsection` | 否 | 仅 `group` 类用：`verify` / `ads` / `stats` / `misc` |
| `featured` | 否 | `true` 进"精选必装"区，全区 ≤ 5 条 |
| `official` | 否 | 人工判断是否官方；抓取拿到的 Telegram 蓝勾优先级更高 |
| `notes` | 是 | 30-60 字中文，写清"核心功能 + 适用场景"，不带链接（链接由 url 自动渲染） |
| `display_name` | 否 | 列表显示名。仅当抓取到的标题为西里尔字母或含杂乱符号时填写，留空则用平台标题清理后显示 |

顶层字段 `featured_order`（可选）：精选区展示顺序数组，元素为带 `@` 的 username。声明后必须**恰好列出所有 `featured=true` 的条目**，`--check seed` 会校验集合一致；不声明则沿用月活降序。当前顺序以 `@soso`、`@BotFather` 打头。

### 抓取字段（由 `scripts/fetch_bots.py` 维护，贡献者勿改）
`fetch` 对象：`status`（`ok`/`dead`/`error`/`pending`）、`http_code`、`fetched_at`、`title`、`description`、`monthly_users`（int）、`type`（`bot`/`channel`/`group`/`user`/`unknown`）、`is_verified`、`photo_url`、`page_kind`（`bot`/`user`/`channel`/`group`/`unknown`）、`not_bot`（bool）、`dead_streak`（连续判定失效次数）、`error_msg`。

新增 bot 时 `fetch` 填 `{"status": "pending"}` 即可，下次抓取脚本会自动填入真实数据。

> ⚠️ **严禁手工填写抓取值**（包括"估算"）：`monthly_users`、`extra_raw`、`fetched_at`、`http_code` 只能由 `fetch_bots.py` 写入。`python scripts/validate.py --check provenance` 会核对 `extra_raw` 与 `monthly_users` 是否可相互反解、`http_code` 是否为 200、时间戳是否具备脚本生成特征（不得整分零微秒、不得多条共享同一时间戳、不得晚于批次时间、顶层批次时间不得与条目时间雷同），以及 `last_verified_label` 是否与批次月份一致。数值有疑问请跑 `python scripts/fetch_bots.py --sleep 2` 全量重抓，**不要手改**。该检查同时由 `.github/workflows/ci.yml` 在每次 PR 时执行。

### 全局字段
`schema_version`（当前 `1`）、`last_fetched_at`（由脚本写）、`last_verified_label`（人类可读核验批次，写进 README 顶部"最近核验"）。

---

## 数据来源

`scripts/fetch_bots.py` 直接抓取 `https://t.me/<username>` 预览页（HTTP 200，服务端渲染，约 11 KB）。不使用 Telegram Bot API，无需任何 token。关键字段位置：

| 字段 | DOM | 示例 |
|---|---|---|
| 显示名 | `<div class="tgme_page_title">…</div>` | `极搜🔍中文搜索@JISO` |
| 自填简介 | `<div class="tgme_page_description">…</div>` | 含 `<br/>`、`<a>`，脚本会清洗成纯文本 |
| 活跃度 | `<div class="tgme_page_extra">…</div>`（页面里有两个该 class，只有含 `monthly users` / `subscribers` / `members` 的那个才是真实数据） | `299 956 monthly users` |
| 官方蓝勾 | `tgme_page_title` 内 `<i class="verified-icon">` | BotFather 有，jiso 无 |
| 头像 | `<img class="tgme_page_photo_image" src="…">` | `https://cdn5.telesco.pe/file/…jpg` |
| 类型推断 | 按 `extra` 文案：`monthly users`=bot / `subscribers`=channel / `members`=group | |
| 页面类型 | 操作按钮：`Start Bot`=bot / `Send Message`=个人账号 / `View in Telegram`、`Join …`=频道或群组 | 非 bot 时 `not_bot=true` |
| 失效判定 | 无 `tgme_page_title` 且为通用页「Telegram: Contact @xxx」（含 "you can contact"），或 HTTP 404 | 记一次失效，`dead_streak+1`；连续 2 次才标 `dead` |
| 异常页 | 无 `tgme_page_title` 但也不是上面的通用页（拦截/验证/异常页），或 429/5xx/网络错误 | 记 `error`，保留上次数据不覆盖 |

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
<!-- AUTO:bots-category:official:start --> … :end -->
<!-- AUTO:bots-category:tools:start --> … :end -->
```

`scripts/render_readme.py` 读 `bots.json` 重写 marker 区块。渲染规则：
- 精选区：表格列 `名称 | 链接 | 一句话用途 | 月活`
- 月活显示：bot `约 30 万/月`、channel `30 万 订阅`、group `30 万 成员`；≥1万用"万"、≥1亿用"亿"
- dead 条目仍显示，加 `❗已失效（YYYY-MM）`；连续 3 次核验失效（`dead_streak ≥ 3`）后自动从 README 和站点隐藏，随后由维护者从 `bots.json` 清理，列表只保留在运营的机器人
- 页面仍存在但已不是 bot（`not_bot=true`，如变为频道/个人账号）：月活列显示 `⚠️已变为频道（非 Bot）` / `⚠️个人账号（非 Bot）`，`validate.py` 会打印警告，需人工复核后移除
- 官方蓝勾或人工 official 在显示名后加 `✓`
- `notes` / `display_name` 中的竖线与换行由 `escape_md_cell()` 统一压平，不会撑破表格；站点的显示名、链接同样做 HTML 转义，只有脚本自己拼的 ✓ 徽标按 HTML 直出
- `category=official` 中 `not_bot=true` 的官方发布频道单独成表并标注「非 Bot · 仅统计订阅数」，不与真正的官方 Bot 混排
- 分类表行序按 `fetch.monthly_users` 降序自动排序；未公开月活（含 <1 万）的条目排在末尾，已失效条目排最后，同档内保持 `bots.json` 原有次序。**因此新增条目不必手动插到合适位置**，渲染时会自动归位
- **精选区例外**：顺序由顶层 `featured_order` 人工指定（编辑精选，与月活高低无关），未写入该数组的精选条目按上述月活降序列在末尾。增删 `featured=true` 条目时必须同步更新数组，否则 `--check seed` 报错；README 与站点两个渲染器共用同一规则

---

## 本地开发

### 依赖
```bash
pip install -r scripts/requirements.txt
```
依赖 `requests` + `beautifulsoup4` + `jinja2`。

### 工作流
```bash
# 1. 改 data/bots.json（新增/编辑 bot 条目）

# 2. 抓取最新元数据（礼貌限流 ≥2s，默认全量重新核验）
python scripts/fetch_bots.py

# 3. 重新渲染 README 与静态站点
python scripts/render_readme.py
python scripts/build_site.py

# 4. 全量自检（退出码 0 才可提交）
python scripts/validate.py
```

`validate.py` 含 7 个子项：
- `--check seed`：bots.json 人工字段完整、id 唯一、category 合法、featured ≤ 5
- `--check readme`：marker 成对、每条 bot 都被渲染、无残留手写链接
- `--check links`：所有 `t.me/xxx` 链接与 json.url 一致
- `--check order`：各分类块确实按月活降序排列（无数据置底、失效最后），手改表格打乱顺序会失败
- `--check dead`：可见的 dead 条目均已附失效标记，已隐藏条目不再渲染
- `--check notbot`：`not_bot` 条目均带 ⚠️ 标记，并打印警告清单（官方频道已单独分组，不作疑似伪装告警）
- `--check provenance`：`fetch` 数据可溯源——`extra_raw ↔ monthly_users` 双向一致、时间戳指纹、批次时间合理，拦截手工编造的活跃度

离线单元测试：`python -m unittest discover -s tests`

无参数 = 跑全部。

### 抓取脚本选项
```bash
python scripts/fetch_bots.py                 # 全量重新核验所有条目（含 dead）
python scripts/fetch_bots.py --id jiso        # 只抓某条
python scripts/fetch_bots.py --only-pending   # 只抓 pending / error 条目（新增 bot 时用）
python scripts/fetch_bots.py --dry-run        # 只打印不写文件
python scripts/fetch_bots.py --sleep 3        # 调整限流（最小 1s 强制下限）
```

幂等保证：新抓结果与旧值完全一致时不刷新单条的 `fetched_at`（因此全量重抓后**多数条目仍保留原抓取时刻**，个别甚至保留更早批次的时间戳；「全量重抓」不等于「全库时间戳统一」，这是预期行为，`--check provenance` 允许）；站点页脚时间取自数据（`last_fetched_at` 日期）而非构建时间，数据不变则 `docs/index.html` 不变。每次全量核验成功后更新顶层 `last_fetched_at` 与 `last_verified_label`（YYYY-MM）。若超过 50% 请求失败（如被 Telegram 限流/拦截），本次视为失败、不写入任何数据，CI 会自动开 Issue。

---

## CI 自动刷新

`.github/workflows/ci.yml` 在每次 **pull_request / push main** 时跑离线单测、`validate.py` 全项（含 provenance）与渲染幂等检查（重渲染后 `README.md` / `docs/index.html` 必须零差异），防止手工编造的 `fetch` 数据或手改表格直接合入。

`.github/workflows/refresh.yml` 每周一 03:00 UTC 自动跑：
1. 离线单元测试（`tests/`）
2. `fetch_bots.py` 全量重新核验所有条目（含已标 dead 的）
3. `render_readme.py` 重写 README
4. `build_site.py` 重建 `docs/index.html`（GitHub Pages 站点）
5. `validate.py` 自检
6. 通过且有变化则 commit+push，失败则自动开 Issue（`auto-refresh-failed` 标签）
7. 刷新完成后由 `.github/workflows/pages.yml` 把 `docs/` 部署到 GitHub Pages（推送 `docs/**` 到 main 或手动触发也会部署）

手动触发可在仓库 Actions 页选 "Bot Data Auto-Refresh" → "Run workflow"。

---

## 收录原则

- **实用**：对中文用户有真实使用价值
- **稳定**：优先长期运营、有月活数据佐证的
- **干净**：不收机场、流量卡、涨粉、博彩拉新、色情导航等灰产类
- **去重**：精选区 ≤ 5 条，分类区按 username 去重
- **失效即清**：连续 2 次核验失效标 `❗已失效`，连续 3 次自动从 README / 站点隐藏，之后由维护者从 `bots.json` 删除，保持列表全部可用
- **月活门槛与例外**：默认只收有公开月活（≥1 万）的条目。确需保留无月活条目，必须满足以下之一，并在 PR 描述中写明理由：① Telegram 官方或带蓝勾、身份可核验的入口；② 中文场景无同类替代；③ 老牌开源、可自建的工具。当前保留 4 条例外：`@wallet`（更名中的官方钱包入口）、`@FeedReaderBot` / `@flowerss_bot`（老牌 / 开源 RSS）、`@TransChat_bot`（群聊上下文翻译）。例外条目在表中自动置底；不满足门槛又无理由的新增会在审阅时退回
- **AI 类慎收**：AI 机器人迭代太快，`category=ai` 可用 `url=null` 占位（只渲染散文引导，不固定具体账号）

---

## 许可证

本仓库所有内容（README、data、scripts、本文档）采用 [MIT License](./LICENSE)。贡献内容同协议。

---

## 致谢

本仓库参考了社区优秀列表（itgoyo/TelegramBot、AZeC4/TelegramBot 等）在选品上的积累，并在结构、活跃度核验、自动维护上做了差异化。

**觉得有用请点个 Star ⭐，让更多人看到这个列表。**