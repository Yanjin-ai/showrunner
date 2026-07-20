# AI Showrunner — 系统设计完整汇报

> 对应代码全部在 `showrunner/`,每一条都可在源码中核对。诚实标注:✅ 已实现并验证 / 🟡 已实现未经额度验证 / ❌ 设计中未实现。

## 1. 总体架构(七层)

```
入口层    CLI (scripts/run.py) · Web App (server.py + templates/index.html)
编排层    Showrunner 状态机 (orchestrator.py) — 并行·重试·关卡·事件·预算
Agent 层  Planner · Storyboard · PromptWriter(纯代码) · Critic · Localizer
契约层    schemas.py — 所有跨层数据都是 Pydantic 模型,强校验
能力层    clients/{qwen,video,image,tts} · consistency · ffmpeg_utils · subtitle_render
状态层    store.py (runs/ 运行态) · assetlib.py (library/ 持久资产)
基建层    QwenCloud OpenAI 兼容端点 · DashScope 异步视频 · 阿里云 ECS
```

依赖单向向下;`orchestrator` 是唯一知道全流程的模块,其余组件无状态、可单测、可替换。

## 2. 数据流转(每一跳的数据形态与归宿)

| # | 数据 | 生产者 | 形态 | 落盘 |
|---|---|---|---|---|
| 1 | brief + genre | 人 | 字符串+枚举 | events.jsonl |
| 2 | StoryBible + scenes(四拍) | Planner | JSON(强校验) | story_bible.json / scenes.json |
| 3 | ShotSpec[](beat/景别/机位/台词/连续性) | Storyboard | JSON | shots.json |
| 4 | 角色参考帧 | Consistency | png → data URI | refs/<char>.png + library/ |
| 5 | VideoGenRequest(prompt包) | PromptWriter | JSON | 内存(可由3+4重建) |
| 6 | task_id → video_url → mp4 | video client | 异步任务 | shots/<id>_tryN.mp4 |
| 7 | QAReport(三轴分+建议) | Critic | JSON | shots/<id>_qaN.json |
| 8 | master → 字幕轨 → final | Editor+Localizer | mp4/srt/json | master.mp4, subs_*.srt, subtitles.json, final.mp4, cover.png, edl.json |
| 9 | 成本明细 | CostTracker | JSON | cost.json |

两条正交流:**数据向下**(brief→成片)沉淀为文件;**控制向上**(审批/评审判决/重试/预算停机)收敛到编排器。

## 3. Agent 分工与"谁用模型、谁不用"

| Agent | 模型 | 温度/模式 | 职责 | 为什么这么配 |
|---|---|---|---|---|
| Planner | qwen3.7-max | 0.5 · json_object | 四拍剧本圣经+角色卡 | 创意质量决定上限,用最强模型 |
| Storyboard | qwen3.7-max | 0.5 · json_object | beats→镜头语言 | 需要电影语法专业度 |
| **PromptWriter** | **无(纯代码)** | — | ShotSpec+资产→视频prompt | 确定性拼装,零 token 零延迟零漂移 |
| Critic | qwen3.6-plus(VL) | 0.2 | 三帧质检+修改建议 | 低温度保证评分稳定 |
| Localizer | qwen3.7-max | 0.5 · json_object | 整批台词一次翻译/语言 | 批量调用省 token |
| Consistency | wan2.7(t2v) | — | 铸定妆帧(库未命中时) | 最贵调用,库命中则跳过 |
| Editor | 无(ffmpeg/Pillow) | — | 拼接/烧字幕/封面/混音 | 本地免费 |

## 4. 模板化 vs 生成(边界清晰)

**模板(代码里固定,零 token):** 六题材剧作手册(GENRES:冲突结构+内容安全边界)、题材专属视觉风格表(GENRE_STYLES)、四拍 JSON 骨架(hook/friction/spike/button + 时间戳)、负向提示词、prompt 组装模板、QA rubric、字幕样式、封面版式。

**生成(模型创作):** 具体剧情/反转、角色姓名与外观描述、台词、每镜头动作/情绪/连续性、翻译、QA 分数与修改建议。

原则:**结构是模板,内容是生成**——保证专业性和稳定性,同时保留创意空间。

## 5. 系统 Prompt 设计(逐 agent)

统一原则:`职业人设 + 领域规则 + 硬输出约束`,全部要求 "ONLY a single valid JSON object"。

- **Planner**:"veteran showrunner for VERTICAL 9:16…four-beat engine…cliffhanger button…two central characters"(职业身份+行业规律),模板注入题材手册与母语台词要求。
- **Storyboard**:"director translating scenes into shots…speak film grammar 景别/机位/blocking/continuity…lives in faces"(镜头语言+竖屏偏特写+"暗示不直给"规避审核)。
- **Critic**:"strict QA reviewer…low scores are useful"(反谄媚设计,鼓励打低分),rubric 明确三轴定义与阈值,产出 revision_advice 必须"concrete, targeted"。
- **Localizer**:"subtitle localizer for streaming short dramas"(保持字幕短促口语)。

## 6. 与 Qwen/DashScope 的交互协议(实测得出)

**文本/VL(OpenAI 兼容端点):**
- 首选 `response_format={"type":"json_object"}` 强制合法 JSON;失败自动降级为低温度普通模式 + `_repair()`(去 // 注释、尾逗号)+ 最外层大括号截取;最终 Pydantic 强校验,不合规即重试——**脏数据永不入流水线**。
- VL 评审**一次请求带 3 帧**(首/中/尾),640px JPEG data URI——视觉 token 是按图算的,压缩即省钱。

**视频(DashScope 原生异步):**
- `POST /video-synthesis` + `X-DashScope-Async: enable` → task_id → `GET /tasks/{id}` 每 8s 轮询,900s 超时;URL 24h 过期 → **成功即下载落盘**。
- i2v 参考图协议(自行探明):`input.media=[{"type":"first_frame","url":<data URI 可用>}]`;合法 type 还有 last_frame/driving_audio/first_clip(唇同步/跨镜衔接的钩子已存在)。
- 韧性:submit 3 次指数退避重试、poll 容忍瞬断、download 3 次重试;上传图片先压缩(参考帧 1080/q88≈300KB,评审帧 640/q82≈100KB),根治并行写超时。

## 7. 质量监控(闭环)

```
生成 mp4 → 抽3帧 → Qwen-VL 按 rubric 打分
  三轴: narrative_alignment(≥5) · character_consistency(≥6) · technical_quality(≥6)
  ├─ 全过 → 收片 + QAReport 落盘
  └─ 不过 → revision_advice 定向回灌 PromptWriter → 重生成(全流程 ≤2 次)
失败兜底(fail-open): critic 报错→保留片子不丢;两次都不过→保留最优一版;
绿网审核拦截→重试一次,再拦→用上一次成功版本。宁可低分成片,不可无片。
```
实测证据:一镜头 character_consistency **1→9**(评审发现主体错误→定向重生成);另一镜头评审精准指出"中途插特写违反固定中景"并给出可执行修改建议。NA 阈值(5)低于 CC/TQ(6),因为单帧序列对"动作完成度"判断天然偏保守。

## 8. 风格一体化(三层叠加)

1. **风格 DNA 注入**:`StoryBible.style`(题材专属:萌宠=暖金,灵异=冷蓝绿+单暖光…)拼进**每一个**镜头 prompt——全片同一调色/光感/镜头质感。
2. **外观全量复述**:出场角色的 dense appearance descriptors 每个 prompt 完整重复(文本级一致)。
3. **定妆帧锁脸**(i2v 模式):角色唯一参考帧作 first_frame,跨镜头同脸同装(实测 cc=9-10)。
负向提示统一压制:模糊/闪烁/畸变/水印/多余字幕。

## 9. 系统记忆与留存(支持碎片化)

**两级记忆:**
- **运行级** `runs/<id>/`:全部中间产物 JSON + `events.jsonl`(append-only 事件溯源,dashboard 即由它折叠渲染)+ 全部媒体。
- **项目级** `library/`(跨运行持久记忆):角色(锁定定妆照+多语音色+版本)/风格 DNA/世界元素;新角色自动写回,下次生成**按 id 直接复用**。

**碎片化留存 = 是,天然支持。** 每个镜头独立留存 `_try1.mp4 / _try2.mp4 / _qa1.json / .frames/`——可以只取某一镜头的某一次尝试;失败运行的可用镜头照样入库(110141 那次 6 镜头成 4,4 个照常出成片)。任何粒度(单帧/单镜/单场/成片/单语言字幕轨)都可独立读取和复用。

**存储选型:纯文件+JSON,无数据库。** 优点:可回放、可 diff、可 git、debug 直观;代价:无并发写锁(单机单编排器场景下成立)。

## 10. 延续性生成的 Cache 策略

**已实现的缓存:**
| 层 | 机制 | 省什么 |
|---|---|---|
| 角色定妆照 | library/ 命中即跳过铸造(`ref_reused`事件) | **每角色省 1 次视频生成**(最贵项) |
| 运行内参考帧 | data URI 内存缓存,N 镜头共享 | 重复编码/IO |
| 镜头级产物 | 通过的镜头永不再触碰 | 重试只花在失败镜头 |
| 中间产物可重建 | VideoGenRequest 可由 ShotSpec+库确定性重建 | 无需缓存 prompt 本身 |

**未实现(诚实,也是最值得做的下一步):**
- ✅ **断点续跑(resume)**:`Showrunner.resume(run_id)` — 复用全部 QA-passed 镜头,只重生成缺失/失败的;regen 失败自动回退最优旧片。CLI `--resume RUN_ID`,dashboard「⟳ Resume」按钮,POST `/runs/{id}/resume`。
- ✅ **字幕缓存**:重剪/重生成时 used-shot 列表未变则直接复用已翻译字幕轨(实测二次 resume 全程 $0)。
- ❌ LLM 响应缓存(同 brief 重规划会重复扣 token)。
- ❌ 跨运行叙事记忆("前情提要"注入,做续集时需要)。

## 11. 成本 Tradeoff(怎么省、怎么停)

**计量与硬停** (`cost.py`):每次调用按类计费(text/vl 按 usage tokens,video/image 按次,tts 按字符)→ 线程安全累加 → 超预算抛 `BudgetExceeded` 立即停机;明细落 cost.json,dashboard 侧栏实时显示。

**结构性省钱设计(比计量更重要):**
1. **PromptWriter 不用 LLM** — 每镜头省一次调用,还消除 prompt 漂移;
2. **上下文瘦身** — Storyboard 只拿 beats 不拿全 synopsis;Critic 只拿本镜头 spec 不拿全剧本;Localizer 每语言一次批量翻译;
3. **视觉 token 压缩** — 评审帧 640px(视觉 token 按图计价);
4. **重试上限 ≤2 + 通过即缓存** — 失败预算有界;
5. **模型分层可配** — Max(创作)/Plus(快任务)/VL(评审),env 一键切换;
6. **json_object 模式** — 解析失败率≈0,消灭"重试整个大 prompt"这一隐性成本。

**实测量级**:6 镜头 i2v 成片 ≈ 8 次视频生成 + ~12 次文本/VL 调用;**视频占总成本 ~95%**——所以一切优化优先砍视频次数(库复用定妆照、有界重试、镜头数控制)。

## 12. 自动化能力分级

| 级别 | 任务 |
|---|---|
| **全自动**(关卡之间零人工) | 四拍剧本、分镜、prompt 组装、参考帧、视频生成、排队/超时/审核兜底、三帧质检、**重试决策**、拼接、双语烧字幕、多语软轨、翻译、封面、成本核算 |
| **人工关卡**(3 处,超时自动放行) | 大纲审批 → 分镜审批 → 成片审批 |
| **人工前置**(一次性) | API key/额度、部署、(可选)上传角色参考 |
| **暂缺自动化** | (已全部补齐:单镜重生成 + 断点续跑均已上线) |

## 13. 诚实的缺口清单(优先级排序)

1. ~~resume/断点续跑~~ ✅ 已实现并验证(复用 passed 镜头、attempt 编号续接、成本合并);
2. ~~单镜头重生成按钮~~ ✅ 已实现并验证(POST /runs/{id}/shots/{sid}/regenerate + UI ↻ Regen,quota 失败自动回退旧片);
3. 🟡 **image/TTS 客户端** — 接口已写好,等额度探 API 形态(各 ~几次调用);
4. ❌ LLM 响应缓存与跨运行叙事记忆;
5. ❌ 配乐生成(QwenCloud 无此模态,计划用无版权曲库)。
