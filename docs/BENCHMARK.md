# 对标调研综合报告:成熟视频生产体系 vs 我们的 Showrunner

> 调研时间 2026-07。四路并行深挖,全部原始报告(含 80+ 经核实链接)在 [docs/research/](research/):
> [LTX Studio](research/ltx-studio.md) · [Runway](research/runway.md) · [Google Flow](research/google-flow.md)
> · [Showrunner/HeyGen/Hedra](research/showrunner-heygen-hedra.md) · [Kling/Hailuo/Vidu](research/kling-hailuo-vidu.md)
> · [Sora 设计尸检(已停服)](research/sora.md)
> · [专业影视管线 ShotGrid/ftrack/Frame.io/OTIO](research/film-pipeline.md)
> · [工程体系 ComfyUI/Netflix/Temporal/VBench/LiteLLM](research/pipeline-engineering.md)
> · [中国短剧工具链 即梦/可灵/Vidu/剪映/工作室实践](research/cn-short-drama.md)

## 一、全行业收敛的 10 个共识模式

1. **资产先行 (Asset-first)**。所有头部产品把「角色/场景/道具/风格」做成一等实体库:LTX Elements
   (@-tag + 服装变体 + 改一处全传播)、Runway References(@提及 + 输出可回存为参考)、Flow
   Ingredients(≤3/镜)、Vidu My References(≤7 主体)、可灵主体库、即梦全能引用(9图+3视频+3音频)。
   中国工作室实践更直接:「生成完所有概念图,短剧工作已完成 80%」——资产层决定质量上限。
2. **结构先审、后渲染 (Structure-first gate)**。LTX 在渲染任何一帧前展示完整可编辑的场/镜结构
   ("this is where the budget is protected");HeyGen Agent 先出可编辑 Plan 再渲染;Boords 用免费
   animatic 锁节奏。最便宜的否决点放最前。
3. **便宜预览 → 昂贵提交 (Cheap-preview-before-commit)**。Runway Edit Studio:5-20 credit 改静帧、
   看 before/after、才花 28 credit/s 渲视频;LTX Generate(预览) vs Apply(提交)双按钮;Netflix
   VVS(廉价规格校验)先于 VQS(感知质量分)。
4. **生成前显示确切价格**。Flow 在 prompt 框设置里直接显示当前配置的 credit 价;Vidu 把实时价格
   写进 Generate 按钮("12 credits ($0.06)");Runway Act-Two 弹时长-价格确认框。另配「慢队免费档」
   (Hailuo Relax Mode / Vidu off-peak)承接抽卡式迭代。
5. **镜头生命周期状态机 + 版本栈**。ShotGrid:任务态 `wtg/rdy/ip/fin` 与制品审批态 `rev/apr` 两轴,
   Version 转 Final 自动晋级 Shot;**角色门禁状态迁移**(只有主管能 rev→apr);ftrack「建版本即入审」
   + 版本号涨到 approved 才停;Frame.io 版本栈浮动 current 指针,评论钉在具体版本。
6. **续接双原语 (Extend vs Jump-To)**。Flow 把镜头续接收敛成两个动词:Extend(取上镜最后一秒续动作)
   与 Jump To(切新场景保角色)。Vidu 首尾帧接续、Runway "Use Current Frame" 同构。
7. **段内定向重拍 (Retake)**。LTX 旗舰功能:选 2–16s 片段 → 只重写该段 prompt → 模型顾及上下文帧
   重生成。"fix the line reading, not the scene"。
8. **运镜三层控制**。预设档(Kling Master Shots / LTX presets)→ 结构化参数档(Kling 六轴 ±滑杆 /
   Runway 六轴 −10..+10)→ DSL 档(Hailuo `[推进][跟随]` 方括号内联指令,palette 点选插入、文本可编辑、
   API 可回环)。
9. **分层质检 (Tiered QA)**。Netflix VVS→VQS;VBench 16 维度各用廉价专用模型(DINO 一致性/CLIP
   对齐/RAFT 光流)先跑,贵的 judge 只看幸存者;LLM-judge 共识:二元判决+rubric 胜过 1-5 分、
   跨模型家族评审、20-50 条金标集校准。
10. **级联预算治理**。LiteLLM 六级预算(全局→团队→key→终端用户)+ 时间窗 + fail-closed;Replicate
    aborted(未开始,零费)vs canceled(已开始,按量)计费语义;单一 choke-point 客户端打标签归因。

**Sora 尸检补充(产品已死,模式无主)**: ①「间距即时序」beat 卡时间轴(卡距近=硬切,留隙=模型
衔接)+「生成转回文本」的素材↔剧本往返;②**迭代阶梯定价**——编辑操作(Remix/Re-cut/Blend/Loop)
按增量微表计价、低于首创,Remix 强度选择器(Subtle/Mild/Strong)把漂移幅度显式化,「15s=2 个视频」
的倍数计价比裸 credits 可读;③角色 = 带 ACL 的可@资产(从任意片段创建、@handle 引用、逐资产权限+
使用通知+可撤销)——班底连续性与肖像合规的一体化蓝本。教训:烧钱无收入模型撑不住(~$1M/天)。

## 二、差距分析:我们 vs 行业

| 维度 | 行业标杆 | 我们现状 | 差距 |
|---|---|---|---|
| 资产库 | @-tag 引用、服装变体、改一处全传播、多模态参考槽 | ✅ 有库(定妆照+音色),i2v first_frame 复用 | 🟡 无 @-引用语法、无变体、无传播更新、参考槽单一 |
| 结构先审 | 渲染前完整可编辑场/镜结构 | ✅ 大纲/分镜双关卡(approve/halt) | 🟡 只能批/停,**不能在关卡里直接编辑结构** |
| 便宜预览 | 静帧先审再渲视频 | ❌ 直接渲视频 | **首帧预览关卡是最大省钱机会**(i2v 本就需要首帧) |
| 价格前显 | 按钮里显示确切价 | 🟡 有事后成本条+预算硬停 | 缺**事前**估价(本次分镜 ≈ $X) |
| 镜头状态机 | wtg/rdy/ip/rev/apr/fin + 版本栈 + 角色门禁 | 🟡 事件折叠出状态;try 编号即版本 | 缺显式状态机、版本栈 UI、当前指针 |
| 续接原语 | Extend / Jump-To 两按钮 | ❌ 无 | last_frame 协议已探明,可低成本落地 |
| 定向重拍 | 段内 Retake | 🟡 有整镜 Regen | 无段内重拍(受限于 API,可后补) |
| 运镜控制 | 预设+滑杆+DSL 三层 | 🟡 prompt 里写运镜 | 缺结构化运镜 UI(ShotSpec.camera 已是字段,好接) |
| 分层质检 | 廉价确定性→专用指标→VL judge | 🟡 直接上 VL 三帧 | 缺 0 成本前置检查(可解码/黑帧/时长)与维度化重试 |
| 预算治理 | 级联+时间窗+admission control | ✅ 单级硬停+计量归因 | 🟡 缺项目/镜头级级联与事前 admission 检查 |
| 时间线/EDL | OTIO 标准、NLE 可导出 | 🟡 自有 edl.json | 可映射 OTIO(镜头 ID/参数进 metadata) |
| 合规 | AIGC 显隐双标识内建导出 | ❌ 无 | 国内分发是硬要求(2026-04 起不合规下架) |
| 协作/审阅 | 帧级批注、per-reviewer verdict、分享链接 | ❌ 单人 | 产品化后需要,hackathon 可缓 |

**我们已领先或对齐的**: 四拍叙事引擎(无人有)、闭环 VL critic+定向重试(多数产品无自动质检)、
断点续跑+字幕缓存(对齐 ComfyUI/Prefect 缓存思想)、预算硬停(多数创作工具只有余额)、多语言本地化。

## 三、设计蓝图:下一代交互 + 灵活控制面

### P0(直接决定体验与成本,优先做)
1. **首帧预览关卡(Frame Gate)** — 每镜头先出首帧图(Qwen-Image I2I,~$0.02)排成 contact sheet,
   人批帧后才渲视频($0.30+)。一次否决省 15 倍成本;正好复用 i2v first_frame 链路。
   UI:Storyboard 标签升级为可批帧的画格墙,每帧 ✓/↻/✎。
2. **镜头状态机 + 版本栈** — 显式 `draft → frame_ready → rendering → review → approved → locked`,
   QAReport/人工批准驱动迁移;镜头卡展开显示 try 栈(当前指针可手动指回旧版);approve 自动晋级。
3. **事前估价 + 级联预算** — Generate 按钮显示「本次 ≈ N 次视频 × $0.30 + …」;预算分
   run/scene/shot 三级,admission 时检查(拒新增,不杀在途)。
4. **续接双原语** — 镜头卡加 Extend(last_frame=上镜尾帧)与 Jump-To(first_frame=角色定妆照+新场景
   prompt)两按钮,协议已验证。

### P1(控制面与质量)
5. **运镜三层控制** — ShotSpec.camera 结构化为 `{preset, axes:{pan,tilt,zoom,…}, dsl}`;UI 给预设
   芯片 + 可选滑杆;prompt_writer 翻译成文字运镜(将来模型支持参数就直传)。
6. **分层质检** — critic 前加 0 成本 deterministic 检查(ffprobe 时长/分辨率/黑帧/解码);QAReport
   已维度化,把重试建议绑定到失败维度;建 20 条金标帧回归测试 critic prompt。
7. **@-引用资产语法** — brief/分镜编辑框支持 `@lin_ye` 自动补全,绑定库内资产;资产详情页支持
   「换定妆照→全片传播」与「Duplicate 服装变体」。
8. **关卡内编辑** — 大纲/分镜关卡从 approve/halt 升级为可直接改字段(改完才放行),对齐 LTX 的
   structure-first 编辑。

### P2(生态与出海)
9. **OTIO 导出**(edl.json→.otio,NLE 可接) · **合规导出**(AIGC 显式片头标识 + 元数据隐式标识)
   · **慢队/快队双档**(闲时免费抽卡档) · 协作审阅(分享链接 + 帧级评论)。

### 架构落点(映射到现有代码)
- 状态机/版本栈 → `store.py` 加 shot_state.json + `server.py` 状态迁移端点(角色门禁留钩子)
- Frame Gate → `consistency.py`/`image.py` 出首帧 + `gates.py` 新关卡类型 `frames`
- 估价 → `cost.py` 加 `estimate(plan)`;级联预算 → CostTracker 加 scope 栈
- Extend/Jump-To → `video.py` 已支持 first/last_frame;`orchestrator.py` 加两个单镜方法
- 运镜结构化 → `schemas.py` CameraSpec + `prompt_writer.py` 翻译层
- 分层质检 → `critic.py` 前置 `precheck()`(纯 ffprobe)
- @-引用 → 前端 autocomplete + `assetlib.py` 查询端点(已有)

## 四、一句话结论

行业已经收敛:**资产库是脊梁、结构先审、帧先于视频、价格先于生成、状态机管生命周期、分层质检管
质量、级联预算管钱**。我们的编排/质检/续跑底子已对齐工程侧最佳实践,最大的两个缺口是
**交互侧的 Frame Gate(便宜预览)与镜头状态机/版本栈**——这两个恰好也是把「能跑」变成「好用的
生产工具」的关键,且全部可在现有架构上增量落地。
