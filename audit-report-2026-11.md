# Telegram Bot 清单审计与替换建议

> 审计时间：2026-11-04（所有月活数字均为当日实时抓取 `t.me/<username>` 预览页所得，非仓库里的旧快照）
> 结论一句话：**没有条目彻底死链，但清单"瘦而不精"——29/70 条查不到任何月活，多个分类的头部（几十万到几百万月活）整体缺席。**
> 按你的要求：本报告不改仓库，只给结论 + 可直接照做的替换清单；收录取向按月活优先、但**中文/英文可用**为门槛（俄语/西里尔界面 Bot 一律标注或降级）。

---

## 0. 审计口径与方法

| 项 | 做法 |
|---|---|
| 月活数据 | 实时抓 `https://t.me/<username>` 服务端渲染页，取 `tgme_page_extra` 的 `N monthly users`；频道取 `subscribers` |
| 连通性 | 同上，HTTP 200 且页面存在 `tgme_page_title` 视为存活；409/404 与泛型 "Telegram: Contact @x" 页视为死链 |
| 交叉验证 | Charlie Morrison 2026-10 系列实测（[群管 115 个](https://charliemorrison.dev/blog/telegram-bots-for-groups-2026/)、[AI 91 个](https://charliemorrison.dev/blog/telegram-ai-bots-2026/)、[翻译 78 个](https://charliemorrison.dev/blog/telegram-translator-bots-2026/)、[转换 96 个](https://charliemorrison.dev/blog/telegram-converter-bots-2026/)），以及 [Guo-astro/awesome-telegram](https://github.com/Guo-astro/awesome-telegram)、[redkio/Telegramchannel](https://github.com/redkio/Telegramchannel) 两份中文/英文清单 |
| 覆盖 | 现有 70 条全部重验 + 新增候选 218 个 |

一句提醒：Telegram 预览页月活是"规模"不是"质量"排名，但它确实是唯一可自动化、可复现的客观信号，也正好是 README 自己写的筛选标准。下面凡标「✅实测通过」的，都有第三方 2026-10 的实操记录，不只是月活高。

---

## 1. 先说最扎眼的问题：三个分类的"天花板"被整个跳过

这不是个别条目选得差，是**分类级的选品失焦**。

| 分类 | 当前最大月活 | 行业实际头部 | 差距 |
|---|---|---|---|
| AI 助手 | **空表**（只留了一句"自己搜关键词"） | @GPT4Telegrambot 508.8 万 | 完全没有主力 |
| 群组管理 | @shieldy_bot 20.7 万 | @GroupHelpBot 236.0 万 / @MissRose_bot 233.9 万 | 一个数量级 |
| 频道推送 | @postbot 247.9 万 | 已接近头部，无缺口 | — |
| 搜索发现 | @soso 116.6 万 | 已接近头部 | — |
| 加密交易 | @solana_trojanbot 4.1 万 | @CryptoBot 123.7 万 | 两个数量级 |

加密那栏尤其典型：收了 4 个 Solana 土狗狙击 Bot（全是 1.6–4.1 万月活），却漏掉 Telegram 生态里最大的支付/钱包入口 @CryptoBot（123.7 万）。

---

## 2. 必须处理：3 条已死链

| 条目 | 分类 | 实测 | 处理 |
|---|---|---|---|
| @apkdl_bot | 实用工具 | 页面已被回收，无标题无描述 | **删**。替换 → @uploadbot（1.9 万，URL 直传 Telegram，单文件 500MB）或直接改指 Google Play 官方 |
| @soula | 搜索发现 | 已失效 | **删**。同类中文搜索保留 @jiso（41.5 万）、@aiso（2.0 万）即可 |
| @autoforwardroxybot | 频道推送 | 已失效 | **删**。替换 → @controllerbot（28.6 万，频道排版+统计，ChatKeeper 实测为可用 Bot） |

> 注：这三条在仓库快照里都还是 `status: ok`，说明每周巡检没有覆盖到"页面还在但内容空了"的情况。

---

## 3. 高月活但名不副实：4 条该迁走或改造

这几条不算死链，但**放在当前分类里会误导读者**。

| 条目 | 分类 | 实测 | 问题 | 建议 |
|---|---|---|---|---|
| @premium | 官方 | 637.3 万订阅 | 是**频道**不是 Bot，且已有 @PremiumBot(679.3 万) 承担同样职能 | **删**（或并入 @PremiumBot 备注） |
| @TAndroidAPK | 官方 | 26.0 万订阅 | 同上，是频道 | 保留但明确标「频道」，或与 @tgx_log 合并为一行 |
| @tgx_log | 官方 | 6.3 万订阅 | 同上，是频道 | 同上 |
| @cctv365bot 未收录 / @sotv | 搜索 | 6.2 万 | @Cctv365bot 与 @sotv 是**同一个 Bot**（标题、描述、月活完全一致），只收了一个 | 现状正确，别再当两条收 |

---

## 4. 需要降级或替换的"零月活 / 超低月活"条目

以下 29 条查不到任何公开月活。它们不一定坏，但按 README 自己写的"按真实月活排序"标准，它们全在垫底区，且其中相当一部分有更好的替代。

### 4.1 建议直接删除（10 条，功能已被覆盖或过时）

| 条目 | 理由 | 替换 |
|---|---|---|
| @freqrobot | 无月活、无更新、限流功能被群管套件覆盖 | @nmnmfunbot（85.1 万，中文，含限流） |
| @WatchDoorBot | 标注 beta 多年、无月活、仅按消息类型封禁 | @daysandbox_bot（英文，新号 24h 内发链即删）✅实测通过 |
| @AutoRestrictBot | 同样 beta 挂多年 | @daysandbox_bot 或 @GroupHelpBot |
| @AntiHyperlinkBot | 单一功能、无月活 | 保留（功能独特）但降到组内末位 |
| @AntiServiceMessageBot | 单一功能、无月活 | 同上 |
| @adnamekillerbot | 无月活、无描述、无头像 | @tlgbot 类中文广告杀手 → 建议换 @GuangGaoShaShouBot |
| @adzhongjiezhe_bot | 无月活、只有一句交流群链接 | @fangzhang_bot（21.7 万，中文，垃圾信息拦截） |
| @littleGuardianBot | 无月活、挂在第三方托管 | @join_captcha_bot（1.8 万）✅实测通过 |
| @groupattendancebot | 无月活、停更 | @jung2_bot（冗PowerBot，群发言统计） |
| @kingdk_bot | 无月活 | 保留（中文考勤无同类替代）但在分类末位 |

### 4.2 建议替换（有明确上位替代）

| 条目 | 现月活 | 替换为 | 新月活 | 备注 |
|---|---|---|---|---|
| @P4CaptchaBot | 1.17 万 | @Customize_Captcha_Bot | **16.8 万** | 同为中文界面验证码，ChatKeeper 实测通过 |
| @joinhider_bot | 1.10 万 | 保留 | — | 功能独特（删进退群提示），无可替代 |
| @toorucaptchabot | 无月活 | @Customize_Captcha_Bot | 16.8 万 | 同一用途 |
| @tgcnjoincaptchabot | 无月活 | @WatchdogVerifyBot | 3.4 万 | 开源反机器人验证 |
| @FengDoorBot | 无月活 | @fangzhang_bot | 21.7 万 | 大掌门同作者生态，功能更全 |
| @FengStatsBot | 无月活 | @tgstat_bot | 8.0 万 | 群/频道统计 |
| @policr_bot | 无月活（页内劝退，导向 mini 版） | @policr_mini_bot | — | 官方自己让你改用这个，别再收老号 |
| @TransChat_bot | 无月活 | @translategooglero_bot | — | ✅实测为唯一说明"使用 Google API"的翻译 Bot |
| @TranslateBot | 无月活 | @perevodchik_bot | — | 实测同一引擎家族，翻译质量优于前者 |
| @bilibiliparse_bot | 无月活 | @ParsehubBot | — | 中文多平台解析，覆盖面更广 |
| @freedlvideo_bot | 无月活 | @kaczyn_bot | — | 20+ 平台无水印，✅实测通过 |
| @aliyunshare_bot | 无月活、停更 | @AliYunPanBot 保留一条即可 | — | 两条阿里云盘 Bot 冗余 |
| @cnLottery_bot | 无月活 | @tgdraw_bot | — | ✅实测（giveaway/poll/quiz 一体） |
| @qiandaobot | 无月活 | @ttjfree_bot 保留 | — | 二选一 |
| @inlinegamesbot | 无月活 | @BoardingGames_bot | — | 国际象棋/2048/数独等，活跃维护 |
| @teletarotbot | 无月活 | 保留 | — | 中文塔罗无同类 |
| @BrightwoodBot | 无月活 | 保留 | — | 英文文字冒险，无同类 |

---

## 5. 应该补进来的头部条目（缺口最大的先列）

### 5.1 AI 助手 —— 这是全清单最大的空洞

分类现在是空的。以下按"中文/英文可用"过滤后保留（俄语系但英文界面可用的标注出来）：

| Bot | 月活 | 语言 | 说明 |
|---|---|---|---|
| @GPT4Telegrambot | **508.8 万** | 英/中/俄 | 聚合 ChatGPT+Claude+Gemini+DeepSeek+Midjourney，账号体系成熟；实测 1 次免费后要求订阅频道换 50 次/周 |
| @gpt3_unlim_chatbot | **270.6 万** | 英/中/俄 | 按额度计费（约 0.0025 卢布/条），实测连续 6 条未撞墙 |
| @gpt5tgbot | 24.0 万 | 俄（英文可用） | 多模型聚合 |
| @trendyai_bot | 5.4 万 | 英 | 带图片编辑 |
| @DeepSeekBot(@deepseekai_bot) | 无数据 | 英/中 | 中文语料强，DeepSeek 官方风格命名 |

**注意**：@CopilotOfficialBot 虽然带蓝勾，但微软已于 2026-01-15 下线第三方 IM 接入，实测 `/start` 至今无响应，**别收**。@GrokAI 同理静默。

### 5.2 群组管理 —— 现清单缺头部整整一个数量级

| Bot | 月活 | 语言 | 说明 |
|---|---|---|---|
| @GroupHelpBot | **236.0 万** | 英/多语 | 群管套件事实标准，✅实测通过 |
| @MissRose_bot | **233.9 万** | 英 | 老牌 mod bot，权限/规则/反刷齐全，✅实测通过 |
| @nmnmfunbot | **85.1 万** | **中文** | 中文群管第一，✅实测通过 |
| @ChatKeeperBot | 54.5 万 | 英 | 审核+统计+验证码+欢迎语一体，✅实测通过 |
| @fangzhang_bot | 21.7 万 | **中文** | 验证/欢迎/广告拦截/定时/强制订阅 |
| @KinhRoBot | 16.2 万 | 中文 | 群管+免费 AI 对话 |
| @WeGroupRobot | 13.6 万 | 英 | 群管套件 |
| @WatchdogVerifyBot | 3.4 万 | 多语 | 开源反机器人入群验证 |
| @Customize_Captcha_Bot | 16.8 万 | **中文** | 自定义题库验证码 |
| @daysandbox_bot | 无数据 | 英 | 新号 24h 发链即删 ✅ |

> 五个 @GHClone1Bot 之类的克隆不必单收，@GroupHelpBot 主号即可（克隆合计 799 万，属同一体）。

### 5.3 加密交易

| Bot | 月活 | 说明 |
|---|---|---|
| @CryptoBot | **123.7 万** | Telegram 内建支付/钱包事实标准，Crypto Pay 商户接口 |
| @wallet | 蓝勾 | TON 官方钱包（Walt），150M 用户量级 |
| @bananagunbot | — | EVM 狙击，实测生态活跃（预览页指向聊天频道，需标注） |

### 5.4 频道推送 / 搜索 / 工具

| Bot | 月活 | 说明 |
|---|---|---|
| @livegrambot | 104.7 万 | 双向反馈 Bot 生成器，频道主必备 |
| @like | 56.4 万 | 帖子表情回应按钮 |
| @controllerbot | 28.6 万 | 频道富文本+统计 |
| @discussbot | 3.6 万 | 帖子评论按钮 |
| @SearcheeBot | 25.4 万 | 频道检索 |
| @telemetr_io_bot | 18.2 万 | 频道数据核实 |
| @tgstat_bot | 8.0 万 | TGStat 数据 |
| @vkmusic_bot | **214.7 万** | 音乐检索下载 |
| @TrueMafiaBot | 94.9 万 | 群内狼人杀 |
| @newfileconverterbot | 5.8 万 | 文件格式转换 ✅ |
| @pdfbot | 1.8 万 | PDF 处理 |
| @username_bot | 1.5 万 | 蓝勾，抢注用户名 |
| @fragment | 29.3 万 | 蓝勾，Fragment 拍卖提醒 |
| @VoiceMsgBot | 1.2 万 | 语音转文字 |

---

## 6. 分类结构建议

1. **拆出「文件与转换」**：转换/PDF/OCR/转写现在混在"实用工具"里，跟天气、词典抢位置，体量与稳定性都不同档。
2. **「实用工具」改名「效率工具」**并赶走一次性玩具（@dicbot、@WeatherBot 无数据但保留，@apkdl_bot 删）。
3. **官方分类只放 Bot**：@premium / @TAndroidAPK / @tgx_log 三条频道移出，另起「官方频道」或在表内用频道图标标识（仓库已有 `not_bot` 标记能力，渲染层做区分即可）。
4. **AI 分类重建后加一句免责**：所有 AI Bot 都会在 2–4 条后立频道墙或收费墙，且会瞎报日期——README 里应该写死这点，而不是留一句"自己搜"。

---

## 7. 执行顺序（若你决定动手）

1. 删 3 条死链 + 2 条 Telegram 频道冗余 → 跑 `fetch_bots.py` 全量确认
2. 删 4.1 的 10 条 → 跑 `validate.py --check order`
3. 补 5.1 AI 分类（先 5 条，`featured` 给 @GPT4Telegrambot）
4. 补 5.2 群管头部 → 群管精选从 @combot 换成 @GroupHelpBot
5. 补 5.3/5.4 → 跑 `build_site.py` + 测试
6. 精选区整体重排（现精选的 @instasave_bot 仅 6.4 万，是五个精选里最弱的一环）

---

### 附：本次实测的完整新候选月活（供你二次核对）

```
GroupHelpBot 2 359 841 | MissRose_bot 2 339 360 | vkmusic_bot 2 146 731
CryptoBot 1 237 301 | livegrambot 1 046 963 | TrueMafiaBot 949 211
nmnmfunbot 851 362 | like 563 941 | ChatKeeperBot 544 872 | GPT4Telegrambot 5 072 246
gpt3_unlim_chatbot 2 706 172 | fragment 292 922 | controllerbot 286 197
SearcheeBot 253 955 | gpt5tgbot 239 761 | fangzhang_bot 217 444
telemetr_io_bot 182 241 | Customize_Captcha_Bot 167 749 | KinhRoBot 161 933
WeGroupRobot 135 968 | newfileconverterbot 58 044 | trending: trendyai_bot 54 486
username_to_id_bot 53 690 | WatchdogVerifyBot 33 770 | discussbot 35 830
deepseek_gidbot 35 035 | dogeindexbot 22 119 | join_captcha_bot 17 936
pdfbot 18 124 | uploadbot 18 830 | skeddybot 17 125 | username_bot 14 852
querytokenbot 14 865 | VoiceMsgBot 12 438 | telemetr 182 241
```
