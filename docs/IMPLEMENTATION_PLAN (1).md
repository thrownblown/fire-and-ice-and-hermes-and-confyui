# Fire & Ice — Implementation and Production Plan v0.3

**Scope:** build one coherent local system, prove it on a short sequence, then use measured evidence to expand to the complete film. This is a build plan; no renderer, hardware benchmark, film analysis or generated clip has been executed as part of this document revision.

Read [project intent](Ref2V_AI_Project_Brainstorming.md), then [SYSTEM_CONTRACT.md](SYSTEM_CONTRACT.md). Use the owning subsystem document for details. The archive is outside the active instruction path.

## 1. Small deployable shape

Start with one Python package, one SQLite project database, local immutable artifact storage, a simple local review web app, and a ComfyUI adapter. Commands may be exposed by a CLI and a local HTTP API using the same application handlers. Bind local services to loopback initially.

Suggested package boundaries are `core`, `media`, `perception`, `identity`, `references`, `planning`, `renderers/comfy`, `evaluation`, `editorial`, and `memory`. These are modules, not independently deployed services. Use a durable local queue and one GPU lease; no Redis, distributed scheduler, graph database or vector service is needed for the first slice.

Select and lock exact dependency/model versions during implementation qualification. Do not install a vaguely specified “latest” stack and call it reproducible. Keep model artifacts outside source control, addressed by manifest hashes. Project-specific configuration and fixtures remain small and reviewable.

## 2. Order work by risk and useful evidence

| Stage | Build/output | Exit condition |
| --- | --- | --- |
| 0A: feasibility | Host inventory, one pinned H3 profile, complete canary/restart measurements | Actual Ref2VA workload fits and runs; or a precise documented blocker |
| 0B: project foundation | Records/revisions, artifact registry, database migration, commands/events, budget ledger | Import/inspect a synthetic project; stale writes and duplicate commands handled |
| 1: source/time | Master manifest, frame/PTS index, selected audio, cut proposals, exact extraction, TimeMap | Three-to-five adjacent source slots reconstruct with continuous audio and no drift |
| 2: evidence/design | Minimal VLM observations, confirmed needed identities, approved target designs/location | Each required role has evidence/design or an explicit blocker |
| 3: planning/compiler | Contracts, semantic selections, profile capabilities, deterministic graph/prompt compilation | Same pinned inputs produce identical request bytes and a useful validation/source map |
| 4: one full shot | Submit, recover, evaluate, select and export | One actual locally generated shot goes through the whole loop |
| 5: contiguous slice | Shared characters/location, neighboring-shot checks, original audio assembly | Coherent three-to-five-shot sequence; no hidden source placeholders |
| 6: bounded pilot | Six representative cases; at most two conditions; maximum 24 pilot renders | Promote/reject the next useful strategy/profile with cost and quality evidence |
| 7: sequence production | Progressive coverage, scoped memory, cost forecasts, targeted repair | Repeated sequences complete within policy with reviewed continuity |
| 8: feature finishing | Complete assembly, unresolved-defect review, optional selected-take polish, snapshot/export | All intended intervals covered and traceable; complete audio/timing and quality review |

Stages 0A and 0B are independent engineering work, but do not expand GPU-dependent scope until 0A passes. If H3 fails, preserve the local-only requirement and the renderer-neutral contract. Test another local profile/model explicitly; source/identity/corpus work remains reusable.

## 3. Work packages and interfaces

| Package | Consumes | Produces | Critical integration proof |
| --- | --- | --- | --- |
| Core/state | Commands + schema | Revisioned records, events, queue, budgets | Atomic transition; expected-revision conflict; duplicate command replay |
| Media/editorial | Local film + source intervals | SourceMaster, evidence, TimeMaps, assembly | Exact frame extraction; rational mapping; continuous source audio |
| Identity/design | Evidence + cues + curated images | Assertions, DesignSets, SequenceContracts | Mentions never imply visibility; target changes do not rewrite source belief |
| References | Active role needs + source assets | Provenance, derivatives, selections | Asset traceability; duplicate/variant distinction; eligible role selection |
| Perception/planning | Evidence + policy + designs | Observations, ShotContracts, RenderPlans | Targeted field correction; creative freedom; actionable capability conflicts |
| H3 adapter/compiler | Plan + capability/profile | CompiledRequest + Attempt artifacts | Socket/label equivalence, exact consumed frames, memory qualification |
| Evaluation/memory | Output + contract + neighbors | Evaluation, outcomes, scoped recipes | Unknown hard criteria block auto-accept; failures retained; no causal overclaim |
| Review surface | Shared read packets and commands | Human decisions, selection revisions | Same decision semantics through UI and agent commands |

Integration uses one fixture and shared IDs from the start. Do not let each package invent a character ID format, shot duration convention or status enum. The supplied [core schema](contracts/fi_core.schema.json) and [synthetic fixture](examples/probe_cycle.json) establish the first executable boundary.

## 4. The first real vertical slice

Choose a contiguous three-to-five-shot sequence after inspecting the actual master. Prefer one or two recurring characters, one environment, manageable movement, and at least one meaningful audio/continuity obligation. Do not cherry-pick a disconnected beauty shot as evidence that the film pipeline works.

Complete one shot first. Its walk-through must show:

1. Source frame and audio provenance.
2. What the agent believes and one explicit uncertainty or confirmed interpretation.
3. Approved target design and a contract stating what may change.
4. A minimal reference selection with understandable reasons.
5. A compiled request with exact routing/time/profile provenance.
6. Actual measured local execution and technical checks.
7. Contract evaluation and human visual judgment.
8. Selection and insertion into its original editorial slot.
9. A saved outcome/lesson and clean project resume in a new process.

Then complete the neighboring shots using the same approved assets. Include one controlled rejection or targeted repair to demonstrate that feedback is operational; a known synthetic defect can test the application path without wasting an extra GPU render. Do not manufacture a successful artistic result for the demo.

The slice deliverable is a playable sequence, assembly/request manifests, evidence packets, accepted/rejected evaluations, cost report and restorable snapshot. Any mock generation is visibly labeled and cannot satisfy the actual-GPU exit condition.

## 5. Tests tied to material failure modes

| Risk | Required implementation check |
| --- | --- |
| 23.976/24/audio drift | Synthetic rational-clock fixtures and a real contiguous assembly; absolute-boundary quantization |
| Essential reference action truncated | A tail-event fixture whose consumed reference would lose the event; preflight must reject |
| Wrong character reaches a socket | Two clearly distinct asset fixtures; binding manifest matches graph and prompt definitions |
| Repeated expensive execution after timeout | Lose submission acknowledgement; reconciliation adopts the existing job/output before resubmission |
| Concurrent/stranded GPU workload | Lease expiry + worker restart; no overlapping submissions until reconciliation |
| Stale shared design | Update one design revision; only consumers become stale; old selected output remains traceable |
| Fake certainty | Missing/contradictory evidence yields unknown/unresolved, never fabricated confidence |
| Correlated “learning” | Change multiple variables; outcome cannot be promoted as isolated reference causation |
| Failed export hidden by concatenation | Missing slot, stale take, timing gap, bad audio origin and placeholder all cause explicit validation results |
| Project loss | Restore a snapshot and resolve every selected artifact and request |

Use deterministic local checks for schemas, timing, hashes and command semantics. Perceptual quality and real model fit require actual execution/review. Do not add a large low-value unit-test suite around prose-only choices.

## 6. Budget policy and throughput forecasting

[config/bootstrap_policy.yaml](config/bootstrap_policy.yaml) contains explicit bootstrap ceilings. They are policy defaults to tune, not benchmark measurements. Null cost estimates stay null until measured; admission still uses finite canary limits.

Account for:

- model/encoder load and unload time;
- perception, asset generation and H3 occupancy under one GPU lease;
- reference preparation and unused/cropped generated duration;
- successful, failed, canceled and unresolved attempts;
- evaluation and human review time;
- cache/storage growth, I/O and cold restarts.

After the pilot, estimate feature effort using the actual shot-duration/archetype distribution and accepted screen-second yield by qualified profile. Report a range and sample sizes. Do not infer production ETA from a best seed or a hosted latency figure.

Choose sequence-sized batches. If the review queue grows, spend effort resolving it or finish another CPU task rather than creating unlimited unreviewed videos. If a shared design repeatedly causes defects, repair it before rendering all dependent shots.

## 7. Feature-scale expansion without changing architecture

1. Finish a stable sequence and snapshot it.
2. Reuse approved assets; acquire only uncovered references for the next sequence.
3. Update cost estimates and candidate recipes from all outcomes.
4. Promote only qualified changes; keep the prior working profile available.
5. Revisit stale or failed shots through dependency-aware repair.
6. Review sequence boundaries, audio continuity and story state across the feature.
7. Apply optional upscale/deflicker/lip repair only to selected takes where a demonstrated benefit exceeds cost; re-evaluate after every transformative pass.
8. Export a complete manifest and final movie; retain a lossless or suitably high-quality local intermediate where storage permits.

Full-film progress is measured as selected, reviewed editorial duration, with separate counts for unreviewed, blocked and stale coverage. Titles/credits/transitions are explicit editorial units or exceptions, not silently omitted intervals.

## 8. Things to defer until evidence warrants them

Distributed services, autonomous self-modifying instructions, learned reward models, bandits, broad crawling, multiple embedding families, training/fine-tuning, exhaustive cast annotation, compulsory endpoint generation, every H3 variant, cloud oracles, and whole-film upscale passes.

The system remains extensible through versioned contracts and adapters. Extension is justified by a concrete failure or measurable improvement, not by the existence of another component.

## 9. Definition of done

For the application: a fresh agent can orient, inspect evidence, change a target within policy, estimate and submit work, recover an interrupted job, diagnose a result, select and assemble it, and leave a reusable explanation—without undocumented database edits or relying on prior chat context.

For the film: every intended editorial interval is covered by an accepted take or an explicit agreed exception; original audio remains correctly aligned; identities/story/continuity meet the active contracts; no required unresolved defects or hidden placeholders remain; and the final movie is reproducible at the manifest/workflow level from a restorable project. Exact neural byte-for-byte replay is not promised across different hardware or runtime versions.
