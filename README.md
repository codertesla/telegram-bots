# 中文 Telegram 机器人索引

> 按真实月活与场景筛选，每周自动验活，剔除死链与伪装频道

收录 **9 大高频场景、66 个在运营 Bot**。所有条目由脚本每周抓取 Telegram 公开月活数据（MAU）并核验连通性，助你快速定位可用的群管、检索、解析与效率工具。

<!-- AUTO:last-verified:start -->
> 最近核验：2026-11
<!-- AUTO:last-verified:end -->

## 核验标准

- **真实月活排序**：直接抓取 Telegram 官方预览页披露的月活数据（MAU），主力工具与长尾玩具一目了然
- **每周自动验活**：GitHub Actions 定期巡检，自动剔除停运死号、个人账号及伪装成 Bot 的频道
- **精选一锤定音**：精选区每个核心场景仅保留 1 个月活最高且确认存活的入口，省去横向试错成本
- **单一数据源维护**：全表由 `data/bots.json` 自动渲染生成，杜绝手动改表遗留的失效死链

## 目录索引

- [核验标准](#核验标准)
- [快速上手](#快速上手)
- [精选必装](#精选必装)
- [分类索引](#分类索引)
  - [官方账号](#官方账号)
  - [搜索发现](#搜索发现)
  - [群组管理](#群组管理)
  - [解析下载](#解析下载)
  - [AI 助手](#ai-助手)
  - [多语翻译](#多语翻译)
  - [签到打卡](#签到打卡)
  - [频道推送](#频道推送)
  - [游戏娱乐](#游戏娱乐)
  - [实用工具](#实用工具)
- [安全边界](#安全边界)
- [提交贡献](#提交贡献)
- [维护记录](#维护记录)
- [开发参考](#开发参考)
- [开源许可](#开源许可)

## 快速上手

**私聊调用**

1. 在 Telegram 顶部搜索框输入机器人用户名（如 `@BotFather`）
2. 打开对话页，点击底部 **开始**（**Start**）即可激活指令菜单

**拉入群组**

1. 先私聊目标机器人并点击一次 **Start**（未激活过的机器人可能无法在群内搜到）
2. 打开群组信息页 → 点击 **添加成员** → 输入机器人用户名并选中添加
3. 进入群组 **管理员设置**，按其功能授予最小必要权限（入群验证与反垃圾类通常需开启「删除消息」与「封禁用户」）
4. 如需机器人读取群内普通发言（如关键词拦截、自动翻译），在对话中发送 `/setprivacy` 并设为 `Disable`

## 精选必装

覆盖 5 个最高频场景（官方 / 搜索 / 群管 / 下载 / 娱乐），每类仅取当前月活最高且核验存活的 1 个主力入口。

<!-- AUTO:bots-featured:start -->
| 名称 | 链接 | 一句话用途 | 月活 |
|------|------|------------|------|
| BotFather ✓ | [@BotFather](https://t.me/BotFather) | 创建机器人、配置命令菜单与签发 API Token | 约 796.6 万/月 |
| SOSO搜搜 | [@soso](https://t.me/soso?start=a_6480909132) | 按关键词检索中文群组、频道与音视频资源 | 约 116.6 万/月 |
| Combot | [@combot](https://t.me/combot) | 集成员审核、活跃度分析、反垃圾与自动回复于一体的群管套件 | 约 84.0 万/月 |
| InstaSave: Instagram & TikTok Downloader | [@instasave_bot](https://t.me/instasave_bot) | 解析下载 Instagram、TikTok、X、Facebook 与 Pinterest 图文视频 | 约 6.4 万/月 |
| Quiz Bot ✓ | [@quizbot](https://t.me/quizbot) | 创建多媒体选择题竞赛，支持群内实时抢答与排行榜统计 | 约 162.0 万/月 |
<!-- AUTO:bots-featured:end -->

## 分类索引

### 官方账号

Telegram 官方维护的建号、会员、贴纸、蓝标认证、解封申诉与客户端分发入口。

<!-- AUTO:bots-category:official:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| BotFather ✓ | [@BotFather](https://t.me/BotFather) | 创建机器人、配置命令菜单与签发 API Token | 约 796.6 万/月 |
| Premium Bot ✓ | [@PremiumBot](https://t.me/PremiumBot) | 开通或赠送 Premium 会员（解锁双倍限额、4GB 上传与专属星标） | 约 679.3 万/月 |
| Telegram Premium ✓ | [@premium](https://t.me/premium) | Premium 会员新功能演示与权益说明官方频道 | ⚠️已变为频道（非 Bot） · 637.3 万 订阅 |
| Stickers Bot ✓ | [@Stickers](https://t.me/Stickers) | 创建、导入自定义贴纸包并查看使用统计 | 约 65.1 万/月 |
| Verify Bot ✓ | [@VerifyBot](https://t.me/VerifyBot) | 公共频道、群组与机器人的官方蓝标认证申请入口 | 约 1.9 万/月 |
| Spam Info Bot ✓ | [@SpamBot](https://t.me/SpamBot) | 查询账号受限原因、提交解封申诉与举报垃圾信息 | 约 3428.4 万/月 |
| Telegram APKs for Android ✓ | [@TAndroidAPK](https://t.me/TAndroidAPK) | Android 客户端官方 APK 直装包发布频道 | ⚠️已变为频道（非 Bot） · 25.9 万 订阅 |
| Telegram X APKs & Build Info ✓ | [@tgx_log](https://t.me/tgx_log) | Telegram X 客户端构建日志与安装包发布频道 | ⚠️已变为频道（非 Bot） · 6.3 万 订阅 |
<!-- AUTO:bots-category:official:end -->

### 搜索发现

按关键词检索中文群组、频道、影视、网盘与音视频资源。

<!-- AUTO:bots-category:search:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| 极搜中文搜索 | [@jiso](https://t.me/jiso?start=a_6480909132) | 跨群组、频道、影视、音乐与新闻的综合中文检索 | 约 40.0 万/月 |
| 一起搜电影 | [@sotv](https://t.me/sotv) | 检索电影与剧集资源，支持挂载至群聊内直接调用 | 约 6.3 万/月 |
| 阿里云盘搜索机器人 | [@aliyunshare_bot](https://t.me/aliyunshare_bot) | 按关键词检索阿里云盘共享资源与群内投稿 | — |
| 阿里云盘资源 Bot | [@AliYunPanBot](https://t.me/AliYunPanBot) | 阿里云盘资源检索、收藏、订阅与导出 | — |
| Video Search for YouTube | [@youtube](https://t.me/youtube) | 在聊天框内直接检索并分享 YouTube 视频 | 约 22.7 万/月 |
| 神马搜索 | [@smss](https://t.me/smss?start=spread_6480909132) | 按关键词检索关联群组、频道与细分兴趣社区 | 约 81.2 万/月 |
| 超级索引 | [@CJSY](https://t.me/CJSY?start=6480909132) | 多维度检索中文群组、频道与媒体文件 | 约 89.7 万/月 |
| 搜啦资源搜索机器人 | [@soula](https://t.me/soula) | 按关键词检索中文群组与频道公开内容 | 约 2.3 万/月 |
| aiso中文搜索 | [@aiso](https://t.me/aiso?start=telegram_6480909132) | 发送关键词直接匹配公开群组与频道内容 | 约 1.8 万/月 |
<!-- AUTO:bots-category:search:end -->

### 群组管理

拦截水军、外链广告与高频刷屏。中大型群组建议搭配「1 个进群验证 + 1 个广告拦截」组合使用。

<!-- AUTO:bots-category:group:start -->
**进群验证**

| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| 入群验证机器人 | [@P4CaptchaBot](https://t.me/P4CaptchaBot) | 简洁中文图形验证码，开源且支持自建部署 | 约 1.2 万/月 |
| Policr | [@policr_bot](https://t.me/policr_bot) | 支持自定义问答考核与付费入群验证 | — |
| Shieldy | [@shieldy_bot](https://t.me/shieldy_bot) | 老牌轻量入群验证，超时未验证自动移出 | 约 20.1 万/月 |
| 大掌门 | [@FengDoorBot](https://t.me/FengDoorBot) | 入群验证、进群欢迎语与消息定时自毁（开源） | — |
| Pay Bot | [@feeMasterBot](https://t.me/feeMasterBot) | 付费入群核验，按门槛筛选付费社群成员 | — |
| TGCN-CAPTCHA加群验证 | [@tgcnjoincaptchabot](https://t.me/tgcnjoincaptchabot) | 中文入群验证码核验，自动拦截批量脚本账号 | — |
| OrgRobot | [@orgrobot](https://t.me/orgrobot) | 新成员入群身份核验与准入考核 | 约 3.4 万/月 |
| 天童AL-1S | [@toorucaptchabot](https://t.me/toorucaptchabot) | 多题型强化入群验证，拦截机器号批量加群 | — |
| LittleGuardian | [@littleGuardianBot](https://t.me/littleGuardianBot) | 轻量入群验证与新成员准入控制 | — |

**广告拦截**

| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| TGCN-币&黄广告专杀 | [@adnamekillerbot](https://t.me/adnamekillerbot) | 识别并踢除挂有长用户名广告的水军账号 | — |
| 广告终结者_Bot | [@adzhongjiezhe_bot](https://t.me/adzhongjiezhe_bot) | 按自定义关键词规则自动拦截群内广告 | — |
| AntiHyperlinkBot | [@AntiHyperlinkBot](https://t.me/AntiHyperlinkBot) | 自动删除群聊中包含外部链接与超链接的消息 | — |
| Protectron | [@ProtectronBot](https://t.me/ProtectronBot) | 外链过滤、反刷屏与违规广告自动拦截 | 约 9.7 万/月 |
| Auto Restrict Bot [beta] | [@AutoRestrictBot](https://t.me/AutoRestrictBot) | 自动限制新入群成员的初期发言与发图权限 | — |
| FreqRobot | [@freqrobot](https://t.me/freqrobot) | 限制单用户高频连发消息，防止恶意刷屏 | — |

**活跃统计**

| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| 统计秘书 | [@FengStatsBot](https://t.me/FengStatsBot) | 统计群内发言频次与成员活跃度排行 | — |
| SangMata | [@SangMata_BOT](https://t.me/SangMata_BOT) | 追踪并查询群成员的历史昵称与用户名变更记录 | 约 14.5 万/月 |
| joinhider_bot | [@joinhider_bot](https://t.me/joinhider_bot) | 自动删除成员进群与退群的系统提示消息 | 约 1.1 万/月 |

**秩序维护**

| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| Watch Door [beta] | [@WatchDoorBot](https://t.me/WatchDoorBot) | 按消息类型（贴纸、转发、外链等）自定义封禁规则 | — |
| AntiServiceMessageBot | [@AntiServiceMessageBot](https://t.me/AntiServiceMessageBot) | 自动清理置顶、进退群等系统服务通知，保持版面整洁 | — |
<!-- AUTO:bots-category:group:end -->

### 解析下载

提取主流社媒与视频平台无水印内容，支持私聊发送链接或挂载至群内解析。

<!-- AUTO:bots-category:download:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| 多平台解析下载机器人 | [@freedlvideo_bot](https://t.me/freedlvideo_bot) | 解析下载 X、YouTube、B站、抖音、小红书与 Instagram 视频 | — |
| AI在线解析视频 (DC5) | [@bilibiliparse_bot](https://t.me/bilibiliparse_bot) | 解析下载 B站及主流视频平台无水印内容 | — |
| YoutubeDL - YouTube Download Bot | [@YtbDownBot](https://t.me/YtbDownBot) | 按分辨率提取并下载 YouTube 视频与音频 | 约 4.6 万/月 |
<!-- AUTO:bots-category:download:end -->

### AI 助手

AI 对话类 Bot 迭代与停运极快，固定收录极易失效。建议直接在 Telegram 搜索框检索以下关键词，按当月活跃度挑选：

- `ChatGPT` / `Claude` / `DeepSeek` / `Grok`

优先选择支持「自定义系统提示词 + 多轮长上下文 + 视觉/语音输入」的账号；涉及充值或绑定自有 API Key 时，请先核实运营方背景。如果你长期使用某个稳定的 AI Bot，欢迎按下方 [提交贡献](#提交贡献) 补充收录。

<!-- AUTO:bots-category:ai:start -->
<!-- AUTO:bots-category:ai:end -->

### 多语翻译

私聊双向互译与群聊消息实时自动转译，适合多语种社群与跨国协作。

<!-- AUTO:bots-category:translate:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| Google Translate | [@TranslateBot](https://t.me/TranslateBot) | 调用 Google 翻译引擎，支持私聊与群内多语种双向互译 | — |
| Yandex Translate | [@YTranslateBot](https://t.me/YTranslateBot) | 调用 Yandex 翻译引擎，俄语及欧洲语种互译准确度高 | 约 4.2 万/月 |
| Translator | [@TgTranslatorBot](https://t.me/TgTranslatorBot) | 群聊实时翻译，支持 100+ 语种消息自动转译 | 约 2.7 万/月 |
| TransChat - AI Translate | [@TransChat_bot](https://t.me/TransChat_bot) | 结合群聊上下文自动互译多语种对话 | — |
<!-- AUTO:bots-category:translate:end -->

### 签到打卡

群内每日打卡、连续天数统计与考勤汇总，量化社群活跃度与团队出勤。

<!-- AUTO:bots-category:checkin:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| 打卡机器人 免费版 | [@ttjfree_bot](https://t.me/ttjfree_bot) | 群内日常考勤、签到报到与出勤次数统计 | 约 2.2 万/月 |
| 签到机器人 | [@qiandaobot](https://t.me/qiandaobot) | 群内每日打卡、连续签到天数与积分榜统计 | — |
| Group Attendance Bot | [@groupattendancebot](https://t.me/groupattendancebot) | 记录群成员每日出勤状态并生成考勤报表 | — |
| King打卡 | [@kingdk_bot](https://t.me/kingdk_bot) | 上下班打卡记录与工时自动汇总，适合团队考勤 | — |
<!-- AUTO:bots-category:checkin:end -->

### 频道推送

富媒体排版、定时发布队列与跨频道规则转发，适合频道主日常运营。

<!-- AUTO:bots-category:channel:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| Post Bot | [@postbot](https://t.me/postbot) | 编辑含内联按钮的富媒体图文并发布至频道 | 约 249.1 万/月 |
| TelepostBot | [@telepostbot](https://t.me/telepostbot) | 频道图文排版、定时发布队列与浏览数据统计 | 约 53.4 万/月 |
| Channel Help | [@chelpbot](https://t.me/chelpbot) | 频道定时排版、互动数据统计与抽奖管理 | 约 256.4 万/月 |
| Auto Forward Bot | [@autoforwardroxybot](https://t.me/autoforwardroxybot) | 按过滤规则与时间表自动跨频道转发推送内容 | — |
<!-- AUTO:bots-category:channel:end -->

### 游戏娱乐

群内实时抢答、HTML5 对战小游戏与文字冒险，无需跳出聊天窗口即可发起互动。

<!-- AUTO:bots-category:game:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| Gamee ✓ | [@gamee](https://t.me/gamee) | 内置数十款 HTML5 街机与益智小游戏，支持群内实时对战比拼 | 约 28.2 万/月 |
| GameBot ✓ | [@gamebot](https://t.me/gamebot) | Telegram 官方 HTML5 轻游戏合集，支持单人或群聊发起对战 | 约 16.8 万/月 |
| Inline Games | [@inlinegamesbot](https://t.me/inlinegamesbot) | 通过内联模式在任意聊天框直接发起双人棋牌对战 | — |
| TeleTarot | [@teletarotbot](https://t.me/teletarotbot) | 按问题抽取塔罗牌面并生成牌义解读 | — |
| Brightwood Stories | [@BrightwoodBot](https://t.me/BrightwoodBot) | 按钮交互式文字冒险游戏，按分支选择推进剧情 | — |
<!-- AUTO:bots-category:game:end -->

### 实用工具

一次性临时邮箱、词典、天气、安装包提取与群内抽奖工具。

<!-- AUTO:bots-category:tools:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| DropMail.me | [@DropmailBot](https://t.me/DropmailBot) | 生成一次性临时邮箱，在对话内直接接收注册验证码 | 约 3.2 万/月 |
| dicbot | [@dicbot](https://t.me/dicbot) | 查询英文单词音标、中英释义与例句 | — |
| Weather bot | [@WeatherBot](https://t.me/WeatherBot) | 按城市名称查询实时天气与未来数日气象预报 | — |
| APK Downloader | [@apkdl_bot](https://t.me/apkdl_bot) | 输入应用包名或链接，直接从 Google Play 提取 APK 安装包 | — |
| Telegram 抽奖助手 | [@cnLottery_bot](https://t.me/cnLottery_bot) | 在群内发起按关键词或口令参与的自动开奖活动 | — |
<!-- AUTO:bots-category:tools:end -->

## 安全边界

- **最小权限原则**：将第三方 Bot 设为群管理员时，仅勾选功能必需的权限（例如验证码 Bot 只需「删除消息」与「封禁用户」，切勿开启「添加管理员」）
- **敏感信息隔离**：切勿在任何第三方 Bot 对话中发送账号密码、登录验证码、助记词或支付凭证
- **异常与失效反馈**：遇到仿冒诈骗账号可直接向官方 [@SpamBot](https://t.me/SpamBot) 举报；发现本列表条目停运，欢迎提交带有 `dead-bot` 标签的 Issue

## 提交贡献

欢迎推荐长期稳定、对中文用户有实际价值的 Bot，完整流程见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

- **提交 Issue**：使用下方模板填写基本信息，并打上对应分类标签
- **提交 PR**：直接在 `data/bots.json` 中新增或修改条目（切勿手动编辑 `README.md` 表格，所有表格均由脚本自动渲染）

```text
名称：
链接（https://t.me/xxx）：
分类：official / search / group / download / ai / translate / checkin / channel / game / tools
一句话功能描述：
是否官方：是 / 否
开源仓库（如有）：
```

## 维护记录

本仓库以 `data/bots.json` 为唯一数据源，每周由 GitHub Actions 自动抓取活跃度并核验失效条目。

- **当前规模**：9 大活跃分类 · 66 个在运营条目（含 5 个精选主力入口）
- **近期迭代**：
  - **2026-11**：精简低质与重复条目（移除停运的 GIF Downloader、重复验证码与抽奖 Bot 等 7 条，73→66）；精选区按各场景最高月活重排（`@BotFather` / `@soso` / `@combot` / `@instasave_bot` / `@quizbot`）；移除无月活的 RSS 分类，新增「官方账号」分类
  - **2026-10**：全量重验所有条目，清理 5 条停运死号与 3 条已转为频道/个人号的失效条目；修复每周巡检仅抓取新条目而不复核存量条目的问题；恢复 `https://t.me/xxx` 标准链接并上线 `bots.json` 自动抓取、渲染与校验管线

## 开发参考

- [Telegram Bot API 官方文档](https://core.telegram.org/bots/api)：协议规范、Webhook 配置与内联模式说明
- [@BotFather](https://t.me/BotFather)：注册机器人账号、配置命令菜单与签发 Token
- [aiogram](https://docs.aiogram.dev/)：基于 Python 异步机制的现代框架，适合构建高并发群管与 AI 机器人
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)：文档齐全、生态成熟的 Python 机器人开发库

## 开源许可

本项目基于 [MIT License](./LICENSE) 开源。如果这份索引帮你省下了检索与试错时间，欢迎点亮右上角 **Star**。

> 连通性与月活数据每周由脚本自动核验更新。第三方 Bot 均由各自开发者独立运营，接入群组前请按需收敛管理员权限。
