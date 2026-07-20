# Professional Production-Tracking Systems — Research (July 2026)

## 1. Autodesk Flow Production Tracking (ex-ShotGrid) — the VFX standard
Docs: help.autodesk.com/view/SGSUB/ENU/ · cloudhelp task/pipeline-steps [fetched] · statuses [fetched]
· client-review-site [fetched] · developers.shotgridsoftware.com (+ /b867b4b0/ Version-vs-PublishedFile)

- **Entity model**: Project → Sequence → Shot (∥ Asset). Shots carry **Tasks** under **Pipeline Steps**
  (canonical: Layout → Animation → FX → Lighting → Comp). **Version** = reviewable render;
  **PublishedFile** = the file downstream tools load (watch vs load split). **Playlists** = dailies;
  **Notes** link to Version+Shot+Playlist simultaneously.
- **Status codes** (default task set): `wtg` Waiting / `rdy` Ready / `ip` In Progress / `fin` Final /
  `hld` Hold / `omt` Omit; review-side `rev` Pending Review / `apr` Approved / `vwd` Viewed.
  Statuses grouped Upcoming/Active/Done.
- **Version review ladder**: Pending Review → Pending Director Review → Final Approved, with a
  **trigger: Version goes Final → Shot status auto-updates** (version status drives shot status).
- **Gating**: (a) upstream/downstream task dependencies ("all upstream approved" = ready queue);
  (b) **role-gated status transitions** (permissions on the transition itself — only supervisors
  can rev→apr).
- **Review**: Playlists → review player (compare modes, annotations); Client Review Site = restricted
  share (password/expiry/download toggles), client notes flow back linked.
- **Versioning**: append-only (`{Shot}_{step}_v###`); filesystem templates enforce naming.

**Steal**: two-axis state (task vs artifact approval) + promote-parent trigger; role-gated transitions;
Version-vs-PublishedFile split (review proxy ≠ master asset).

## 2. ftrack Studio / cineSync
Docs: help.ftrack-studio.backlight.co review-approval / asset-version-review-workflow / managing-statuses
· cinesync.com/manual/latest/ftrack_Integration.html [fetched] · ftrack Python API entity_links

- Statuses assembled into per-schema workflows; documented ladder: Pending Review / Revision Requested /
  **Internal Approved / Client Approved** / On Hold.
- **"First status = ready for review"**: creating a version IS the review request (zero handoff).
- **Version number auto-increments until approved** — the loop terminates only on approval.
- Dependencies: FS/SS/FF/SF types + lag; **versions can depend on versions**.
- Review sessions: per-collaborator **Approved / Require Changes** verdicts preserved individually;
  bulk aggregation rule (any-changes → revise; all-approved → approve); **PDF session report** (audit).
- cineSync: frame-locked synchronized playback; annotations publish back with status updates.

**Steal**: creation-enqueues-review; per-reviewer verdicts + explicit aggregation policy (maps to
multi-judge AI QA); session-as-immutable-report.

## 3. Frame.io (Adobe)
Docs: next.developer.frame.io/platform/v2/manage-version-stacks [fetched] ·
help.frame.io commenting-on-your-media [fetched] · C2C guides · workflow.frame.io · VFX best practices

- **Minimal status**: Needs Review / In Progress / Approved (heavy state lives in the tracker).
- **Comments**: frame-accurate, **range-based (I/O brackets)**, annotations pinned to frames,
  @mentions, **hashtag taxonomy** (#color #vfx → filterable), attachments, mark-completed.
- **Version Stacks**: assets stack with a **cover_asset_id floating pointer** to latest; explicit
  linked list (prev/next); comments live on the specific version they were made on.
- **C2C**: proxies upload while recording — collapse capture→review latency ("day-of, not next-day").

**Steal**: version stack w/ floating current pointer; range comments + hashtag taxonomy as structured,
machine-routable QA feedback; proxy-first review.

## 4. Boords / Storyboarder
- boords.com [fetched]: shot cards + script fields; auto-versioned boards, **compare/restore without
  losing comments**; one-click **animatic** (timed board + audio) so "pacing gets signed off before
  anyone opens an editor"; share-link client review; per-frame status + audit trail; public API+webhooks.
- Storyboarder (wonderunit, OSS): Shot Generator (posable 3D from typed description); exports boards
  to Premiere/FCP/Avid/PDF/GIF — boards born editorial-compatible.

**Steal**: **animatic gate before generation** (cheapest rejection point); comments attach to frame
identity, not file blob; storyboard = valid timeline.

## 5. Traditional concepts worth encoding
- **Dailies**: batch review over curated playlists, not one-off approvals.
- **Turnover & conform**: scheduled frozen-edit handoff via EDL/AAF/XML/OTIO + work orders with handles.
- **Script supervisor / continuity**: a ROLE owning cross-shot consistency — lined script + per-take
  logs → encode as a continuity ledger per scene validated by the QA agent.
- **Show LUT / ASC-CDL / ACES AMF**: one versioned global look + tiny per-shot deltas; never fork the
  global style per shot. (≈ style DNA + per-shot trims.)

## 6. OpenTimelineIO (ASWF)
Docs: opentimelineio.readthedocs.io [fetched] · otio-timeline-structure [fetched] · adapters [fetched]

- Timeline → Stack → Tracks → {Clip, Gap, Transition, nested Stack}; Clip = MediaReference
  (target_url, available_range) + source_range (RationalTime: frame-exact, no float drift);
  **Markers** on time ranges; open `metadata` dict everywhere.
- Adapters: otio_json, otiod/otioz bundles, **CMX 3600 EDL (with ASC_CDL color metadata)**, AAF, ALE,
  FCP XML, FCPX XML, more.

**Steal**: adopt OTIO as the edit schema outright (shot IDs/gen params/approval in metadata, QA flags
as Markers); **MediaReference indirection** = swapping approved v007 for v006 is a pointer retarget,
not an edit change; CDL precedent = per-shot style deltas ride the timeline.

## Synthesis: the prescribed shot lifecycle
1. Shot state machine: `omt/hld` + `wtg → rdy → ip → rev → apr → fin`; `rdy` COMPUTED from upstream
   gates (script locked, board approved, style lock exists).
2. Version submodel: auto-increment, append-only, immutable media + mutable status; creation
   auto-enters Pending Review; stack with floating current pointer; `{shot}_{step}_v###`.
3. Review gates at three altitudes: animatic sign-off → internal dailies (per-reviewer verdicts,
   any-rejection-blocks) → client approval via restricted share.
4. Feedback = structured data: frame/range-anchored, tagged, linked, aggregated into immutable reports.
5. Global locks: show LUT ≈ versioned style lock; script supervisor ≈ continuity ledger + QA role;
   turnover ≈ frozen OTIO snapshot dispatching work orders.
