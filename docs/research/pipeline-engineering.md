# Mature Engineering Systems for AI Media Pipelines — Research

Research date July 2026. **[fetched]** = verified by direct retrieval.

## 1. ComfyUI — node-graph orchestration
- https://docs.comfy.org/specs/workflow_json [fetched] · /development/comfyui-server/comms_routes [fetched]
  · /development/comfyui-server/execution_model_inversion_guide [fetched]
- github.com/Comfy-Org/ComfyUI execution.py · deepwiki.com/comfyanonymous/ComfyUI/2.4-caching-system
  · github.com/SaladTechnologies/comfyui-api

**Two JSON formats**: rich UI workflow JSON (nodes, links, positions, widgets) vs minimal **API prompt
format** `{node_id: {class_type, inputs}}` with `[source_node, slot]` refs — the execution wire format:
diffable, hashable, validatable.
**Headless API**: POST /prompt → prompt_id; WebSocket events `status/execution_start/executing/progress/
executed/`**`execution_cached`**; GET /history/{id}; queue inspect/clear; interrupt.
**Subgraph caching (key mechanism)**: per-node cache key = recursive hash of the node's inputs AND its
entire ancestor chain; unchanged signature → cached output reused, node skipped, `execution_cached`
emitted. `IS_CHANGED` = escape hatch for external state. Backends: CLASSIC / LRU (`--cache-lru N`) /
RAM_PRESSURE / NONE. Lazy evaluation + runtime node expansion (loops).

**Steal**: (a) authoring-format vs execution-format split as recipe-as-config wire format;
(b) content-addressed node outputs by recursive input signature = continuable generation (only dirty
subgraphs recompute); (c) explicit "skipped because cached" telemetry so a re-run's true cost is
visible before running.

## 2. fal.ai & Replicate — inference platforms
- https://fal.ai/docs/model-apis/model-endpoints/queue [fetched] · docs.fal.ai webhooks · fal.ai/pricing
- https://replicate.com/docs/topics/predictions/lifecycle [fetched] · /docs/topics/webhooks · /docs/reference/http

**fal**: everything via queue.fal.run — submit returns `{request_id, response_url, status_url,
cancel_url, queue_position}` (**HATEOAS: response carries all follow-up URLs**). States: IN_QUEUE
(+position) / IN_PROGRESS (+logs) / COMPLETED (+inference_time). **Header-based QoS knobs**:
X-Fal-Request-Timeout, X-Fal-Queue-Priority, X-Fal-Runner-Hint, X-Fal-No-Retry. Webhooks: 15s timeout
then 10 retries over 2h. Typed cancellation outcomes.
**Replicate**: starting → processing → `succeeded | failed | canceled | aborted`; **aborted (before
processing) costs nothing; canceled (after start) bills actual runtime** — billing-aware terminal states.

**Steal**: (a) recipe vs QoS-policy as separate layers; (b) self-describing task URLs stored with the
submit response; (c) killed-before-spend vs killed-after-partial-spend distinction for budget attribution.

## 3. Netflix media pipeline (netflixtechblog.com)
- /the-netflix-cosmos-platform-35c14d9351ad [fetched]
- /rebuilding-netflix-video-processing-pipeline-with-microservices-4e5e6310e359 [fetched]
- /the-making-of-ves-… · /netflix-conductor-… · /achieving-observability-in-async-workflows-…

**Cosmos** = 3 layers per service: Optimus (API) / **Plato (forward-chaining rule engine — rules in
Emirax DSL with `match/action/reaction/error` sections)** / Stratum (serverless functions), joined by
Timestone priority queuing. Rules fire when facts change (vs procedural task lists).
**2024 rebuild**: six single-responsibility services — Inspection, Complexity Analysis, Ladder
Generation, **Encoding (VES)**, **Validation (VVS)**, **Quality (VQS/VMAF)**. **Two orchestrators
(Streaming vs Studio) compose the SAME services with different trade-offs.** VES chunk model: split →
31 parallel invocations → assemble → validate; callers see one job. CAS+LGS emit content-dependent
"recipes" (per-shot params). Every encode passes **VVS (cheap spec check) then VQS (perceptual score)**.

**Steal**: (a) draft-vs-final = different orchestration profiles over identical steps; per-step declared
failure handler; (b) per-shot chunks as the retry/idempotency unit, immutable artifacts by ID;
(c) two-stage gate: deterministic checks BEFORE spending on perceptual/VL scoring.

## 4. Temporal / Prefect / LangGraph — durable orchestration
- https://docs.temporal.io/encyclopedia/workflow-message-passing [fetched] · /ai-cookbook/human-in-the-loop-python
- https://docs.prefect.io/v3/concepts/caching [fetched]
- https://docs.langchain.com/oss/python/langgraph/interrupts [fetched] · reference interrupt API

**Temporal**: Queries (read) / Signals (async writes, replay-safe) / **Updates (sync writes with a
VALIDATOR that can reject, plus return value)**. `wait_condition()` suspends server-side; durable
timers survive deploys — waiting is free.
**Prefect**: task cache keys from **composable policies**: DEFAULT / INPUTS / TASK_SOURCE /
FLOW_PARAMETERS, with algebra (`TASK_SOURCE + INPUTS`, `INPUTS - 'debug'`), `cache_expiration`,
isolation levels + lock managers.
**LangGraph**: `interrupt(payload)` pauses; checkpointer (PostgresSaver) snapshots每 super-step keyed by
**thread_id ("persistent cursor")**; resume via `Command(resume=value)`. Gotcha: node re-executes from
top on resume — pre-interrupt code must be idempotent.

**Steal**: (a) approve/reject gate as an Update-with-validator (synchronous accept/reject + reasons);
(b) cache-policy algebra for step caching (seed in/out of key = explicit policy); (c) thread_id-as-cursor
+ checkpoint per stage → "continue this half-finished episode" is a resume, not a re-run.

## 5. GenAI evaluation / quality gates
- https://github.com/Vchitect/VBench [fetched] · arxiv 2411.13503 (VBench++) · arxiv 2503.21755 (VBench-2.0)
- docs.anthropic.com develop-tests · braintrust.dev what-is-llm-as-a-judge · hamel.dev llm-judge
  · OpenAI cookbook custom-llm-as-a-judge

**VBench**: 16 disentangled dimensions (Quality: subject/background consistency, flicker, motion
smoothness, dynamic degree, aesthetic, imaging | Semantic: object class, action, color, spatial,
scene, style, consistency), each scored by a purpose-fit cheap model (DINO subject-consistency, CLIP
alignment, RAFT optical flow…), normalized and aggregated. `--mode=custom_input` scores arbitrary
videos on 6 prompt-free dimensions. VBench-2.0: +18 dimensions (Human Fidelity, Physics, Commonsense…).
**LLM-judge consensus**: layered gates (deterministic → model → sampled human); **binary/rubric beats
1–5 scales**; CoT then discard, keep verdict; **judge from a different model family**; calibrate on a
20–50-item golden set; store human corrections as few-shot examples.

**Steal**: tiered gate (free deterministic → cheap specialist metrics → VL judge only on survivors);
per-dimension scores so retries are targeted; quality_gate as config
`{checks:[...], judge:{model,rubric,threshold}, max_retries}`; golden set to regression-test the critic.

## 6. Cost / token governance
- https://docs.litellm.ai/docs/proxy/users [fetched] · /proxy/provider_budget_routing
- openrouter.ai provisioning-api-keys · api limits · docs.helicone.ai openrouter

**LiteLLM**: six-level cascading budgets (global → team → member → user → virtual key → end-customer);
`max_budget` + `budget_duration` + tpm/rpm/parallel limits; team overrides personal; spend = running
Postgres counter; descriptive 429 on exceed; `fail_closed_budget_enforcement`; **multiple concurrent
windows on one key ($10/day AND $100/month)**; zero-cost models stay accessible after exhaustion;
budget-aware provider routing.
**OpenRouter**: key-per-end-user with own limit from a shared pool; usage rollups; auto-disable;
402 vs 429. **Helicone**: gateway interposition + header-tagged attribution.

**Steal**: hierarchy global→project→scene→shot-attempt with soft-alert vs hard-refuse thresholds;
meter at one choke-point client with tags (episode/shot/attempt/model); pre-flight estimate against
remaining budget; admission-refusal vs let-in-flight-finish.

## Cross-cutting synthesis
1. **Recipe-as-config control plane**: ComfyUI API format + Cosmos match/action/reaction/error +
   fal header QoS + Netflix multi-orchestrator profiles.
2. **Continuable generation**: recursive input-signature caches + composable cache policies +
   thread_id checkpoints + immutable per-shot artifacts.
3. **Quality gates**: VVS→VQS two-stage; VBench per-dimension specialists before the VL judge;
   binary verdicts, cross-family judge, golden-set calibration.
4. **Budget governance**: cascading budgets with windows and fail-closed; billing-aware terminal states.
