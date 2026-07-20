# Sora — Storyboard & Editing Design Autopsy (product discontinued)

**关键事实**: OpenAI 2026-03-24 宣布关停;2026-04-26 网页/App 停服;API 2026-09-24 死亡。
以下为"设计尸检"——基于官方停服公告、Wayback 存档的官方帮助文档、当期教程重建。
死因(报道综合): ~$1M/天算力 vs 弱收入、版权/深伪压力、IPO 成本纪律。

## 时间线
2024-12-09 Sora 1(credits制)→ ~2025-02 取消credits改"无限+队列分级" → 2025-09-30 Sora 2
(iOS 社交App+音频+cameos+feed)→ 2025-10-15 Storyboard 回归(15/25s)→ 2025-10-29 非人角色
cameo+Stitch+排行榜+$4/10次加购 → 2025-11~12 风格预设 → 2026-02 真人图生视频(同意声明)+
Extensions → 2026-03-19 完整时间线编辑器 → 2026-04-26 停服。

## 1. Storyboard(核心交互)
- 入口: 底部 composer 的 **Storyboard** 按钮,或任意生成视频上点 **Re-cut**(= 带素材开新 storyboard)。
- 结构: 顶部 caption 卡片 + 下方横向**时间轴**。每卡 = "该时间戳发生什么";卡内容可为**文本/上传图/
  上传视频**;卡操作: 看源素材、**"把生成转回文本"**(反向caption成可编辑prompt——素材↔剧本往返)、
  加caption、删卡。时间轴任意处 **"+"** 插卡。
- **间距即时序(签名交互)**: 拖卡设节奏——卡距越近越可能硬切;留空隙让模型生成衔接;空隙过大则模型
  即兴填料(失败模式)。底部设置: 比例/分辨率/时长(5/10/15/20s)/变体数;lightbox 预览后才提交。
- **Sora 2 双模式**: "frame by frame from scratch" 或 **"describe a scene → 自动生成可编辑
  storyboard"**(剧本→自动分镜→人改→渲染,正是短剧管线);Pro 25s/普通 15s;输出进 Drafts。

## 2. 编辑工具(官方命名)
- **Re-cut**: "S" 快捷键在时间轴上切分,删坏段、拖余段,Sora 补生成填隙。
- **Remix**: 文字描述修改 + **强度选择器 Subtle/Mild/Strong/Custom**(把"稍微改改"变成显式可学习
  的幅度);Sora 2 中 Remix 成为 feed 级社交动词(最多被 remix 排行榜)。
- **Blend**: 两段视频→一段,**influence 曲线**拖拽控制每个时间点两源的占比。
- **Loop**: 拖柄选区,short/normal/long,重生成接缝。
- Sora 2 后继: **Extensions**(Extend→变成新的更长草稿,非破坏性版本);**Editor**(2026-03,帧级
  trim/stitch/重排/导入草稿/向前extend/**段内重prompt**——真 NLE 与生成融合);**Stitch**
  (Drafts→select→stitch→preview,≤60s)。

## 3. 资产管理
- 侧栏库: hover 预览**连播全部变体对比**;Favorites/Uploads/文件夹;Featured+Explore feed
  (默认 opt-out 公开,曾被批评)。任何库内条目都是一等输入(可喂 Remix/Re-cut/Blend/Loop/Storyboard)。
- Sora 2: **Drafts(私有工作台)→ Post(发布)** 干净分离。

## 4. Composer 控制
一行: Preset(风格)/比例(16:9/1:1/9:16)/分辨率(480/720/1080p)/时长/变体数(1v/2v/4v)。
预设: Archival, Film Noir, Cardboard & Papercraft, Whimsical Stop Motion, Balloon World;
自定义预设 = 文本描述+参考图。Sora 2 简化: Portrait/Landscape + 10/15s + Styles tab。

## 5. 成本 UX(存档官方表)
- Sora 1: 成本 = f(分辨率×方向×时长),composer 里 **"?" hover 预先显示**;480p方 5s=20cr →
  1080p宽 20s=2000cr。**变体按独立生成计费**;**Re-cut/Remix/Blend/Loop 按便宜得多的 per-5s 增量
  微表计费——迭代定价低于首创**。Plus 1000cr(720p/5s 上限)/ Pro 10000cr(1080p/20s、5并发、
  无水印)+ **无限 relaxed 队列**(credits 用尽后免费慢队)。无充值无滚存。
- ~2025-02 改为无限生成+按档队列优先。
- Sora 2: 免费+滚动 24h 限额(~30/天);**时长按倍数计**: 15s=2 个视频、25s=4 个(比裸 credits
  可读性强);$4/10 次加购,与 Codex 共享额度,12 个月有效;全部导出带动态水印+C2PA。

## 6. Sora 2 Characters(角色资产的蓝本)
- **Cameo**: 一次性 App 内录像+读活体口令→验证身份+采集长相+声音;**逐资产 ACL**: Only me /
  People I approve / Mutuals / Everyone;使用通知;可随时撤权/删除任何含本人肖像的视频。
- **非人角色**(2025-10-29): 任意视频(相册或草稿,⋯→Create character)→ 可复用可@的角色,
  自己的**显示名+@handle**+独立权限——"你的猫、玩偶、涂鸦或原创角色"。

## 值得偷的模式
1. **间距即时序的 beat 卡时间轴** + 双入口(自动分镜可编辑 vs 逐帧手搭)+ 每卡多模态锚
   (文/图/片段)+ "生成转回文本"的素材↔剧本往返按钮。
2. **迭代阶梯定价**: 编辑类操作(Remix/Re-cut/Blend/Loop)按增量微表计价,低于首创;
   **Remix 强度选择器**把漂移幅度显式化;composer 内预先显示价格;"15s=2 个视频"的倍数比裸
   credits 可读;relaxed 免费慢队接住 B-take 批量渲染。
3. **角色 = 有权限的可@资产**: 从任意片段创建角色、@handle 引用、逐资产 ACL+使用通知+可撤销
   ——剧集班底连续性 + 肖像合规的一体化蓝本。
4. 战略注脚: Sora 已死、其 storyboard 交互模型成为无主之地——这些模式可架在任何现役视频模型上。

## Sources(节选,均已核实)
- help.openai.com/en/articles/20001152(停服公告,live)
- web.archive.org 2025-06 capture: 9957612 generating-videos-on-sora(storyboard/编辑工具原文)
- web.archive.org 2024-12-12 capture: 10245774 billing-credits-faq(完整价格表)+ 2025-02 capture
- web.archive.org 2026-03 capture: 12460853 creating-videos(Sora 2 流程)+ 12593142 release-notes
- datacamp.com/tutorial/sora-ai · shaicreative.ai storyboard tutorial · filmora sora-2-storyboard
  · superprompt.com sora-2 guide · engadget $4 credits 报道
