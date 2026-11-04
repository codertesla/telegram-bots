# 中文 Telegram 电报机器人大全

> 按真实月活与场景筛选，每周自动验活，剔除死链与伪装频道

收录 **11 大高频场景、76 个在运营 Bot**。所有条目由脚本每周抓取 Telegram 公开月活数据（MAU）并核验连通性，助你快速定位可用的群管、检索、解析、AI 助手、链上交易与效率工具。

<!-- AUTO:last-verified:start -->
> 最近核验：2026-11
<!-- AUTO:last-verified:end -->

## 核验标准

- **真实月活排序**：直接抓取 Telegram 官方预览页披露的月活数据（MAU），主力工具与长尾玩具一目了然。各表自动按月活从高到低排列，未公开月活的条目置底、已失效条目排最后，无需人工调序
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
  - [加密交易](#加密交易)
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
| BotFather ✓ | [@BotFather](https://t.me/BotFather) | 创建机器人、配置命令菜单与签发 API Token | 约 799.6 万/月 |
| SaveAsBot | [@SaveAsBot](https://t.me/SaveAsBot) | 提取 Instagram、TikTok、Pinterest 与 Twitter/X 高清图文与无水印视频 | 约 407.0 万/月 |
| Group Help | [@GroupHelpBot](https://t.me/GroupHelpBot) | 全中文交互菜单的综合群管，支持滑动/算术入群验证、自动禁言与日志审计 | 约 236.0 万/月 |
| Quiz Bot ✓ | [@quizbot](https://t.me/quizbot) | 创建多媒体选择题竞赛，支持群内实时抢答与排行榜统计 | 约 162.8 万/月 |
| SOSO搜搜 | [@soso](https://t.me/soso?start=a_6480909132) | 按关键词检索中文群组、频道与音视频资源 | 约 116.7 万/月 |
<!-- AUTO:bots-featured:end -->

## 分类索引

### 官方账号

Telegram 官方维护的建号、会员、贴纸、蓝标认证、解封申诉与客户端分发入口。

<!-- AUTO:bots-category:official:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| Spam Info Bot ✓ | [@SpamBot](https://t.me/SpamBot) | 查询账号受限原因、提交解封申诉与举报垃圾信息 | 约 3441.1 万/月 |
| BotFather ✓ | [@BotFather](https://t.me/BotFather) | 创建机器人、配置命令菜单与签发 API Token | 约 799.6 万/月 |
| Premium Bot ✓ | [@PremiumBot](https://t.me/PremiumBot) | 开通或赠送 Premium 会员（解锁双倍限额、4GB 上传与专属星标） | 约 681.1 万/月 |
| Telegram Premium ✓ | [@premium](https://t.me/premium) | Premium 会员新功能演示与权益说明官方频道 | ⚠️已变为频道（非 Bot） · 636.9 万 订阅 |
| Stickers Bot ✓ | [@Stickers](https://t.me/Stickers) | 创建、导入自定义贴纸包并查看使用统计 | 约 65.2 万/月 |
| Telegram APKs for Android ✓ | [@TAndroidAPK](https://t.me/TAndroidAPK) | Android 客户端官方 APK 直装包发布频道 | ⚠️已变为频道（非 Bot） · 25.9 万 订阅 |
| Telegram X APKs & Build Info ✓ | [@tgx_log](https://t.me/tgx_log) | Telegram X 客户端构建日志与安装包发布频道 | ⚠️已变为频道（非 Bot） · 6.3 万 订阅 |
| Verify Bot ✓ | [@VerifyBot](https://t.me/VerifyBot) | 公共频道、群组与机器人的官方蓝标认证申请入口 | 约 1.9 万/月 |
| Walt (ex. Wallet) ✓ | [@wallet](https://t.me/wallet) | Telegram 官方原生加密钱包，支持免手续费向联系人直接转账 USDT、TON 与 BTC | — |
<!-- AUTO:bots-category:official:end -->

### 搜索发现

按关键词检索中文群组、频道、影视、网盘与音视频资源。

<!-- AUTO:bots-category:search:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| SOSO搜搜 | [@soso](https://t.me/soso?start=a_6480909132) | 按关键词检索中文群组、频道与音视频资源 | 约 116.7 万/月 |
| 超级索引 | [@CJSY](https://t.me/CJSY?start=6480909132) | 多维度检索中文群组、频道与媒体文件 | 约 89.4 万/月 |
| 神马搜索 | [@smss](https://t.me/smss?start=spread_6480909132) | 按关键词检索关联群组、频道与细分兴趣社区 | 约 83.5 万/月 |
| 极搜中文搜索 | [@jiso](https://t.me/jiso?start=a_6480909132) | 跨群组、频道、影视、音乐与新闻的综合中文检索 | 约 41.5 万/月 |
| Searchee Bot | [@searcheebot](https://t.me/searcheebot) | 跨频道全文检索，按关键词定位公开频道与内容 | 约 25.4 万/月 |
| Video Search for YouTube | [@youtube](https://t.me/youtube) | 在聊天框内直接检索并分享 YouTube 视频 | 约 22.7 万/月 |
| Telemetrio | [@telemetr_io_bot](https://t.me/telemetr_io_bot) | 核实频道真实数据与增长曲线，识别刷量账号 | 约 18.2 万/月 |
| TGStat Bot | [@tgstat_bot](https://t.me/tgstat_bot) | 查询任意频道、群组的订阅量与发帖统计 | 约 8.0 万/月 |
| 一起搜电影 | [@sotv](https://t.me/sotv) | 检索电影与剧集资源，支持挂载至群聊内直接调用 | 约 6.2 万/月 |
| 搜啦资源搜索机器人 | [@soula](https://t.me/soula) | 按关键词检索中文群组与频道公开内容 | 约 2.2 万/月 |
| 狗狗索引 - 搜索神器 | [@dogeindexbot](https://t.me/dogeindexbot) | 中文检索频道、群组与机器人，可挂载群内调用 | 约 2.2 万/月 |
| aiso中文搜索 | [@aiso](https://t.me/aiso?start=telegram_6480909132) | 发送关键词直接匹配公开群组与频道内容 | 约 1.8 万/月 |
<!-- AUTO:bots-category:search:end -->

### 加密交易

内建支付钱包与链上代币买卖入口。接入前请先用小额资金测试滑点与提现流程，并确认 Bot 的授权范围。

<!-- AUTO:bots-category:crypto:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| Crypto Bot | [@cryptobot](https://t.me/cryptobot) | Telegram 内建支付与钱包入口，支持 Crypto Pay 收款与转账 | 约 123.7 万/月 |
| Trojan on Solana ✓ | [@solana_trojanbot](https://t.me/solana_trojanbot?start=r-flashbonk) | Solana 链上跟单与极速交易，支持限价单、止盈止损与多钱包管理 | 约 4.1 万/月 |
| GMGN.AI | [@gmgnaibot](https://t.me/gmgnaibot?start=i_JyY0HbjE) | Solana 链上代币行情与一键买卖，支持跟单、限价与止盈止损 | 约 3.3 万/月 |
| Maestro | [@maestro](https://t.me/maestro?start=r-flashbonk) | 以太坊与 Solana 等多链代币狙击买入，支持跟单、限价与自动止盈止损 | 约 2.7 万/月 |
| BONKbot | [@bonkbot_bot](https://t.me/bonkbot_bot?start=ref_xpnm5) | Bonk 生态代币极速买卖，支持限价单、止损与防夹子模式 | 约 1.6 万/月 |
<!-- AUTO:bots-category:crypto:end -->

### 群组管理

拦截水军、外链广告与高频刷屏。中大型群组建议搭配「1 个进群验证 + 1 个广告拦截」组合使用。

<!-- AUTO:bots-category:group:start -->
**进群验证**

| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| Group Help | [@GroupHelpBot](https://t.me/GroupHelpBot) | 全中文交互菜单的综合群管，支持滑动/算术入群验证、自动禁言与日志审计 | 约 236.0 万/月 |
| Shieldy | [@shieldy_bot](https://t.me/shieldy_bot) | 老牌轻量入群验证，超时未验证自动移出 | 约 20.7 万/月 |
| 自訂型入群驗證 | [@customize_captcha_bot](https://t.me/customize_captcha_bot) | 自定义题库入群验证，中文界面并可维护全局黑名单 | 约 16.8 万/月 |
| OrgRobot | [@orgrobot](https://t.me/orgrobot) | 新成员入群身份核验与准入考核 | 约 3.5 万/月 |
| Telegram Watchdog | [@watchdogverifybot](https://t.me/watchdogverifybot) | 开源反机器人入群验证，按行为特征拦截批量注册号 | 约 3.4 万/月 |
| The Join Captcha Bot | [@join_captcha_bot](https://t.me/join_captcha_bot) | 全自动入群验证码，超时未验证自动移出群组 | 约 1.8 万/月 |
| 入群验证机器人 | [@P4CaptchaBot](https://t.me/P4CaptchaBot) | 简洁中文图形验证码，开源且支持自建部署 | 约 1.2 万/月 |

**广告拦截**

| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| nmBot | [@nmnmfunbot](https://t.me/nmnmfunbot) | 中文全能群管，涵盖验证、关键词拦截、限流与自定义回复 | 约 85.1 万/月 |
| ChatKeeperBot | [@chatkeeperbot](https://t.me/chatkeeperbot) | 审核、统计、验证码与欢迎语一体的英文群管方案 | 约 54.5 万/月 |
| 方丈机器人 | [@fangzhang_bot](https://t.me/fangzhang_bot) | 中文群管，进群验证、欢迎语、垃圾拦截、定时发送与强制订阅 | 约 21.7 万/月 |
| KinhRoBot | [@kinhrobot](https://t.me/kinhrobot) | 中文群管套件，附带免费 AI 对话与实用小指令 | 约 16.2 万/月 |
| We Group Bot | [@wegrouprobot](https://t.me/wegrouprobot) | 英文群管套件，反刷屏、规则与成员操作全覆盖 | 约 13.6 万/月 |
| Protectron | [@ProtectronBot](https://t.me/ProtectronBot) | 外链过滤、反刷屏与违规广告自动拦截 | 约 9.5 万/月 |

**活跃统计**

| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| Combot | [@combot](https://t.me/combot) | 集成员审核、活跃度分析、反垃圾与自动回复于一体的群管套件 | 约 85.6 万/月 |
| SangMata | [@SangMata_BOT](https://t.me/SangMata_BOT) | 追踪并查询群成员的历史昵称与用户名变更记录 | 约 14.4 万/月 |
| joinhider_bot | [@joinhider_bot](https://t.me/joinhider_bot) | 自动删除成员进群与退群的系统提示消息 | 约 1.1 万/月 |

**秩序维护**

| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| Rose | [@MissRose_bot](https://t.me/MissRose_bot) | 全球用户量最大的综合群管，支持防刷屏、进群验证、关键词过滤与警告惩罚 | 约 233.9 万/月 |
<!-- AUTO:bots-category:group:end -->

### 解析下载

提取主流社媒与视频平台无水印内容，支持私聊发送链接或挂载至群内解析。

<!-- AUTO:bots-category:download:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| SaveAsBot | [@SaveAsBot](https://t.me/SaveAsBot) | 提取 Instagram、TikTok、Pinterest 与 Twitter/X 高清图文与无水印视频 | 约 407.0 万/月 |
| Music Downloader | [@MusicsHuntersbot](https://t.me/MusicsHuntersbot) | 跨平台音乐搜索与提取，支持按歌名或 Spotify/YouTube 链接下载 320kbps MP3 | 约 15.4 万/月 |
| InstaSave: Instagram & TikTok Downloader | [@instasave_bot](https://t.me/instasave_bot) | 解析下载 Instagram、TikTok、X、Facebook 与 Pinterest 图文视频 | 约 6.4 万/月 |
| YoutubeDL - YouTube Download Bot | [@YtbDownBot](https://t.me/YtbDownBot) | 按分辨率提取并下载 YouTube 视频与音频 | 约 4.6 万/月 |
<!-- AUTO:bots-category:download:end -->

### AI 助手

多模型聚合对话与代码问答。第三方 AI 账号迭代极快且普遍设有免费提问条数或频道订阅门槛（微软官方 `@CopilotOfficialBot` 已于 2026-01 停止 Telegram 接入）；查询实时资讯前可先核对系统时间，涉及充值或绑定自有 API Key 时请确认运营方背景。

<!-- AUTO:bots-category:ai:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| GPT-4 Telegram Bot | [@GPT4Telegrambot](https://t.me/GPT4Telegrambot) | 集成 GPT-4o、Claude 3.5 与 Gemini 的智能对话助手，支持长上下文与语音交互 | 约 508.8 万/月 |
| ChatGPT Unlim Bot | [@gpt3_unlim_chatbot](https://t.me/gpt3_unlim_chatbot) | 多模型聚合对话，按额度计费且免费额度较宽 | 约 270.6 万/月 |
| GPT-5 多模型聚合 | [@gpt5tgbot](https://t.me/gpt5tgbot) | 聚合 ChatGPT、Gemini、Claude 与 Midjourney 的多模型入口 | 约 24.0 万/月 |
| DeepSeek | [@deepseek_gidbot](https://t.me/deepseek_gidbot) | DeepSeek 对话入口，中文语料与代码能力较强 | 约 3.5 万/月 |
<!-- AUTO:bots-category:ai:end -->

### 多语翻译

私聊双向互译与群聊消息实时自动转译，适合多语种社群与跨国协作。

<!-- AUTO:bots-category:translate:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| Yandex Translate | [@YTranslateBot](https://t.me/YTranslateBot) | 调用 Yandex 翻译引擎，俄语及欧洲语种互译准确度高 | 约 4.2 万/月 |
| Translator | [@TgTranslatorBot](https://t.me/TgTranslatorBot) | 群聊实时翻译，支持 100+ 语种消息自动转译 | 约 2.7 万/月 |
| Perevodchik 翻译 | [@perevodchik_bot](https://t.me/perevodchik_bot) | 群聊实时互译，译文质量与语种覆盖较完整 | 约 1.4 万/月 |
| TransChat - AI Translate | [@TransChat_bot](https://t.me/TransChat_bot) | 结合群聊上下文自动互译多语种对话 | — |
<!-- AUTO:bots-category:translate:end -->

### 签到打卡

群内每日打卡、连续天数统计与考勤汇总，量化社群活跃度与团队出勤。

<!-- AUTO:bots-category:checkin:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| 打卡机器人 免费版 | [@ttjfree_bot](https://t.me/ttjfree_bot) | 群内日常考勤、签到报到与出勤次数统计 | 约 2.2 万/月 |
<!-- AUTO:bots-category:checkin:end -->

### 频道推送

富媒体排版、定时发布队列、跨频道转发与评论/回应按钮，适合频道主日常运营。

<!-- AUTO:bots-category:channel:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| Channel Help | [@chelpbot](https://t.me/chelpbot) | 频道定时排版、互动数据统计与抽奖管理 | 约 257.2 万/月 |
| Post Bot | [@postbot](https://t.me/postbot) | 编辑含内联按钮的富媒体图文并发布至频道 | 约 245.0 万/月 |
| Livegram Bot | [@livegrambot](https://t.me/livegrambot) | 免代码搭建双向反馈机器人，解决账号无法主动私聊的问题 | 约 104.7 万/月 |
| LikeBot | [@like](https://t.me/like) | 为频道帖子批量生成表情回应按钮 | 约 56.4 万/月 |
| TelepostBot | [@telepostbot](https://t.me/telepostbot) | 频道图文排版、定时发布队列与浏览数据统计 | 约 54.9 万/月 |
| Controller Bot | [@controllerbot](https://t.me/controllerbot) | 频道富文本排版、内联按钮与发帖数据统计 | 约 28.6 万/月 |
| DiscussBot ✓ | [@discussbot](https://t.me/discussbot) | 为频道全部帖子自动挂载评论按钮，打通讨论组 | 约 3.6 万/月 |
<!-- AUTO:bots-category:channel:end -->

### 游戏娱乐

群内实时抢答、棋牌对战、HTML5 小游戏与文字冒险，无需跳出聊天窗口即可发起互动。

<!-- AUTO:bots-category:game:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| Quiz Bot ✓ | [@quizbot](https://t.me/quizbot) | 创建多媒体选择题竞赛，支持群内实时抢答与排行榜统计 | 约 162.8 万/月 |
| True Mafia | [@truemafiabot](https://t.me/truemafiabot) | 群内狼人杀，身份私聊下发、白天公投处决 | 约 95.3 万/月 |
| Gamee ✓ | [@gamee](https://t.me/gamee) | 内置数十款 HTML5 街机与益智小游戏，支持群内实时对战比拼 | 约 27.7 万/月 |
| GameBot ✓ | [@gamebot](https://t.me/gamebot) | Telegram 官方 HTML5 轻游戏合集，支持单人或群聊发起对战 | 约 16.7 万/月 |
<!-- AUTO:bots-category:game:end -->

### 实用工具

拍卖提醒、跨格式文件转换、一次性临时邮箱、直链转存、PDF 处理与 RSS 订阅工具。

<!-- AUTO:bots-category:tools:start -->
| 名称 | 链接 | 核心功能 | 月活 |
|------|------|----------|------|
| Fragment Auction Alerts ✓ | [@fragment](https://t.me/fragment) | Fragment 拍卖提醒，追踪用户名与礼物成交价 | 约 29.3 万/月 |
| File Converter | [@newfileconverterbot](https://t.me/newfileconverterbot) | 图片、音频、文档的跨格式转换，直接回传转换结果 | 约 5.8 万/月 |
| DropMail.me | [@DropmailBot](https://t.me/DropmailBot) | 生成一次性临时邮箱，在对话内直接接收注册验证码 | 约 3.2 万/月 |
| URL Uploader | [@uploadbot](https://t.me/uploadbot) | 把 URL 直链直接转存为 Telegram 文件，单文件上限 500MB | 约 1.9 万/月 |
| PDF Bot | [@pdfbot](https://t.me/pdfbot) | PDF 瑞士军刀，支持在聊天中合并、拆分、提取文本、加水印与文件转换 | 约 1.8 万/月 |
| Skeddy | [@SkeddyBot](https://t.me/SkeddyBot) | 自然语言定时提醒助手，支持用口语化输入设定待办日程并准时推送 | 约 1.7 万/月 |
| Voice to Text | [@voicemsgbot](https://t.me/voicemsgbot) | 语音与视频消息转文字，支持多语种转写 | 约 1.2 万/月 |
| Feed Reader | [@FeedReaderBot](https://t.me/FeedReaderBot) | 老牌多平台信息流订阅器，监控 RSS/Atom、YouTube 频道与播客更新 | — |
| flowerss | [@flowerss_bot](https://t.me/flowerss_bot) | 高口碑开源 RSS 订阅机器人，支持 Telegraph 页面即时预览排版与 OPML 导入 | — |
<!-- AUTO:bots-category:tools:end -->

## 安全边界

- **最小权限原则**：将第三方 Bot 设为群管理员时，仅勾选功能必需的权限（例如验证码 Bot 只需「删除消息」与「封禁用户」，切勿开启「添加管理员」）
- **敏感信息隔离**：切勿在任何第三方 Bot 对话中发送账号密码、登录验证码、助记词或支付凭证
- **警惕仿冒与频道墙**：同名同图标的克隆号很常见，添加后回群成员列表核对实际入群用户名；遇到以「先订阅频道」换取功能的，按需取舍
- **异常与失效反馈**：遇到仿冒诈骗账号可直接向官方 [@SpamBot](https://t.me/SpamBot) 举报；发现本列表条目停运，欢迎提交带有 `dead-bot` 标签的 Issue

## 提交贡献

欢迎推荐长期稳定、对中文用户有实际价值的 Bot，完整流程见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

- **提交 Issue**：使用下方模板填写基本信息，并打上对应分类标签
- **提交 PR**：直接在 `data/bots.json` 中新增或修改条目（切勿手动编辑 `README.md` 表格，所有表格均由脚本自动渲染）

```text
名称：
链接（https://t.me/xxx）：
分类：official / search / crypto / group / download / ai / translate / checkin / channel / game / tools
一句话功能描述：
是否官方：是 / 否
开源仓库（如有）：
```

## 维护记录

本仓库以 `data/bots.json` 为唯一数据源，每周由 GitHub Actions 自动抓取活跃度并核验失效条目。

- **当前规模**：11 大活跃场景 · 76 个高质量在运营条目（含 5 个精选主力入口）
- **近期迭代**：
  - **2026-11（全站实测复核与头部生态补齐）**：清理 28 个零月活或停更长尾条目，按实时抓取的真实月活补齐 34 个各赛道头部入口（70→76）——群管补入 `@GroupHelpBot`（236.0 万）、`@MissRose_bot`（233.9 万）、`@nmnmfunbot`（85.1 万）、`@chatkeeperbot`（54.5 万）、`@fangzhang_bot`（21.7 万）、`@customize_captcha_bot`（16.8 万）等；启用 AI 分类表格并收录 `@GPT4Telegrambot`（508.8 万）、`@gpt3_unlim_chatbot`（270.6 万）、`@gpt5tgbot`（24.0 万）与 `@deepseek_gidbot`（3.5 万）；新增官方钱包 `@wallet`、加密支付 `@cryptobot`（123.7 万）、社媒提取 `@SaveAsBot`（407.0 万）与 `@MusicsHuntersbot`（15.4 万）、频道运营 `@livegrambot` / `@like` / `@controllerbot` / `@discussbot`、检索与数据核实 `@searcheebot` / `@telemetr_io_bot` / `@tgstat_bot` / `@dogeindexbot`、群狼人杀 `@truemafiabot`（95.3 万）以及工具类 `@fragment` / `@newfileconverterbot` / `@uploadbot` / `@pdfbot` / `@SkeddyBot` / `@voicemsgbot` / `@flowerss_bot` / `@FeedReaderBot`；精选区升级为 `@SaveAsBot` 与 `@GroupHelpBot`，并支持 `display_name` 人工显示名以规整俄文与营销后缀
  - **2026-11**：精简低质与重复条目（移除停运的 GIF Downloader、重复验证码与抽奖 Bot 等 7 条，73→66）；精选区按各场景最高月活重排（`@BotFather` / `@soso` / `@combot` / `@instasave_bot` / `@quizbot`）；移除无月活的 RSS 分类，新增「官方账号」分类；站名改为「电报机器人大全」，搜索分类改按月活降序，精选条目改为在所属分类中一并列出；排序改由渲染器按月活自动完成（无数据置底、失效最后），并新增 `validate --check order` 防回归；新增「加密交易」分类，收录 `@solana_trojanbot` / `@gmgnaibot` / `@maestro` / `@bonkbot_bot` 共 4 个链上交易 Bot
  - **2026-10**：全量重验所有条目，清理 5 条停运死号与 3 条已转为频道/个人号的失效条目；修复每周巡检仅抓取新条目而不复核存量条目的问题；恢复 `https://t.me/xxx` 标准链接并上线 `bots.json` 自动抓取、渲染与校验管线

## 开发参考

- [Telegram Bot API 官方文档](https://core.telegram.org/bots/api)：协议规范、Webhook 配置与内联模式说明
- [@BotFather](https://t.me/BotFather)：注册机器人账号、配置命令菜单与签发 Token
- [aiogram](https://docs.aiogram.dev/)：基于 Python 异步机制的现代框架，适合构建高并发群管与 AI 机器人
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)：文档齐全、生态成熟的 Python 机器人开发库

## 开源许可

本项目基于 [MIT License](./LICENSE) 开源。如果这份索引帮你省下了检索与试错时间，欢迎点亮右上角 **Star**。

> 连通性与月活数据每周由脚本自动核验更新。第三方 Bot 均由各自开发者独立运营，接入群组前请按需收敛管理员权限。
