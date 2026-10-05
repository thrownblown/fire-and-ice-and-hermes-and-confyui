# Fire & Ice — Local H3 Rendering and Experiment Policy v0.3

**Revised:** 2026-09-16. **Authority:** [project design](Ref2V_AI_Project_Brainstorming.md) and [SYSTEM_CONTRACT.md](SYSTEM_CONTRACT.md). This document owns renderer capabilities, qualification, execution profiles, timing realization and bounded render experiments.

## 1. Decision

Begin with local H3-Base Ref2VA, approved target character/location references, and one probe per shot. Include source motion only when it supports the shot contract. Treat FL2VA, additional guides, V2V, acceleration changes and lip repair as alternatives to test against specific defects.

The production target is this user's single RTX 5090 / 64 GB Ubuntu machine. Neither local fit nor feature-length throughput is established by these design documents. Qualify an actual workload before investing in full-film analysis or extensive assets.

MiniMax's public release separates Base generation from hosted Context-IR and Regenerate-2K. Base has separate FL2VA and Ref2VA checkpoints; native output is 24 fps with 32 kHz audio, and its published nominal duration range is 4–15 seconds. These product facts do not establish local memory fit or the capabilities of every adapter. [Official H3 release](https://github.com/MiniMax-AI/MiniMax-H3)

## 2. Separate three decisions

| Decision | Example | Owner |
| --- | --- | --- |
| What control is needed? | Approved identities and environment; free camera; essential action before cut | ShotContract + strategy |
| What can this adapter express? | Ref2VA roles, frame grid, guide support, actual consumed reference length | CapabilityProfile |
| What exact executable configuration runs? | Quantized checkpoint, encoder, VAEs, LoRA, steps, graph and offload configuration | ExecutionProfile |

Agent-facing plans select semantic strategies. They do not casually mutate sampler nodes or substitute checkpoint families. Every low-level change creates a profile revision and identifies which qualification results remain applicable.

## 3. G0: prove feasibility on the actual workstation

Use a pinned native ComfyUI workflow as the first adapter. Do not run the official multi-GPU server recipe unchanged on this machine. MiniMax's deployment guide distinguishes its server baseline from evolving consumer-GPU configurations and quantized/offloaded paths. [Deployment guide](https://platform.minimax.io/docs/guides/local-deploy-h3)

Comfy-Org currently supplies pruned/quantized Ref2VA checkpoints, H3-specific Qwen3-VL-32B encoders including an NVFP4 variant, and VAEs. Its card prefers `int8_convrot` when the compatible CUDA/PyTorch stack is available. These are candidates to qualify, not evidence that an arbitrary combination fits 64 GB RAM or preserves quality. [Comfy model artifacts](https://huggingface.co/Comfy-Org/MiniMax-H3)

Record the following before a model download or long run:

- detected VRAM and total/available host memory in bytes; driver, CUDA/PyTorch, Ubuntu, CPU and GPU identity;
- storage free space, download sizes, model/cache/output reserve, and local I/O throughput;
- exact checkpoint, encoder, tokenizer/processor, video/audio VAE, LoRA and workflow hashes;
- software/node commits, attention implementation, compute dtype, offload and decode behavior;
- intended output dimensions/frame count and the full reference shape, not merely image count.

Start with **one Ref2VA checkpoint**, one compatible H3 encoder, and the required VAEs. Do not download all variants. The external analysis VLM is separate from H3's own encoder; caching shot captions does not eliminate H3 encoding.

The admission policy reserves 10 GiB of detected host RAM and 2 GiB of detected VRAM for system/headroom as initial configurable margins. These are project safety margins, not measured H3 requirements. Evaluate memory peaks across loading, encoding, denoising and decoding, including CPU tensors, pinned buffers, mapped-file residency and temporary copies. Swap thrashing is a failed feasibility result, not a sustainable offload strategy.

Run at most three qualification generations initially: a representative canary, a meaningful prompt perturbation with other controls held fixed, and a repeat after unloading/restart. Begin with the minimal real reference set; qualify the pilot's larger reference shape before admitting it. Use a finite watchdog, initially 1,800 seconds per canary, recorded as a budget choice rather than a speed expectation.

**Pass:** complete valid output; expected prompt sensitivity; references visibly relevant; no sustained swap pressure; measured peaks below policy; clean unload/reload; attributable logs and actual timing. A prompt perturbation requires perceptual inspection—different bytes alone do not prove correct conditioning.

**Fail:** stop admission for that profile and return the bottleneck. Try a compatible, pinned memory-saving alternative or smaller supported reference workload as a new profile. Do not silently drop required identities or lower resolution below a validated regime. If none works, mark local H3 infeasible under current constraints; continue CPU-side project preparation and evaluate a local alternative behind the same contract. Never silently switch to a hosted service.

## 4. Bootstrap strategies

| Strategy ID | Controls | Status and trigger |
| --- | --- | --- |
| `ref2va_identity_environment/v1` | Approved identities, environment; textual action | First baseline for narrative reinterpretation |
| `ref2va_source_motion/v1` | Baseline plus source motion reference and explicit retention | Try when action/order or choreography needs stronger evidence |
| `ref2va_guided/v1` | Ref2VA plus tested target-time guides | Experimental; only for a measured timing/geometry defect |
| `fl2va_endpoints/v1` | Prepared target first/last frames and connecting action | Optional when precise boundaries justify asset work |
| `v2v_controlled/v1` | Source-derived controls in a separately qualified local model | Deferred until a failure makes it worthwhile |

The environment is a Ref2VA semantic reference. It is **not** automatically passed as `first_frame` alongside reference inputs. That older brainstorming recipe mixed incompatible mode assumptions.

Source motion is not an exact rotoscoping guarantee. Its value is an empirical trade-off between action fidelity and unwanted copying of the original visual treatment. A contract permitting new staging may need no source video at all.

## 5. Execution profiles and acceleration

Profile names describe measured configurations, not implied quality ranks. A `local_ref2va_full_sampling` profile can use quantized weights. “Full sampling” is not “full precision,” and neither is a quality oracle without evidence.

Bootstrap with one stable profile. After it works, test one compatible task-specific acceleration adapter against it. An 8-step path is a useful inherited hypothesis; do not make it the mandatory preview or assume preview and final outputs share the same defects. Four-step variants, new attention kernels, guide combinations and control adapters enter only as separately budgeted experiments.

Profiles pin checkpoint family, all artifact hashes, quantization, LoRA task/strength, inference steps, scheduler/sigmas, CFG if applicable, seed handling, dimensions, reference image sizing, frame count, encoder settings, and decode parameters. Record resulting effective values, not just requested values.

Use `reference_image_size=match` as a bootstrap candidate if the chosen adapter supports it. High-resolution references can change both cost and behavior; increasing reference resolution is an intervention to measure. A clean neutral identity crop is often a more useful first test than adding more images.

## 6. Frame-grid and reference preprocessing contract

The inspected ComfyUI implementation aligns output lengths to `17k+5` frames at 24 fps. It marks roughly 124–362 frames as its trained range. It also clips reference video to the output length and then reduces its frame count to the grid; this can discard the end of a supplied motion reference. Its first/last-frame node anchors the final image at `frame_count-1`. Pin this behavior to the installed commit before use. [ComfyUI H3 implementation](https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_minimax_h3.py)

For requested generated duration `T`, calculate with rational arithmetic:

```text
required_frames = ceil(24 * T)
aligned_frames = 5 + 17 * max(0, ceil((required_frames - 5) / 17))
production_frames = max(qualified_profile_min_frames, aligned_frames)
```

Reject a value above the qualified profile maximum; do not invent support by expanding the node's UI range. The initial production minimum is 124 until a shorter workload is qualified. The adapter verifies the decoded output, since a request is not proof of the actual frame count.

Before submitting a reference, publish its preprocessing manifest: source interval/PTS, resampling rule, actual sampled frames, color/crop/resize transforms, padding/trim, audio association, and **effective consumed end**. For example, 100 input frames can become 90 after a downward `17k+5` alignment. If that removes a required action, reject or create an explicit derivative; do not proceed unnoticed.

Possible remedies are text-only action, approved padding with no invented event, different reference duration, or a qualified shorter-reference profile. Each has a recorded trade-off. Never pad by including a neighboring source cut unless a multi-shot reference was deliberately planned.

Hosted product input limits and local implementation acceptance differ. Bootstrap conservatively within the published reference envelope; allow local exceptions only under measured profiles. Node acceptance of a very short clip is not evidence of useful conditioning. [H3 input specifications](https://github.com/MiniMax-AI/MiniMax-H3)

## 7. Editorial duration and original audio

Use the shared `TimeMap`. Generate enough usable material, then choose a keep window whose essential events fit the editorial slot. For a short shot, put the required event in that window; do not generate a five-second action and assume its first two seconds contain the result.

For a long continuous shot, propose overlap segments and test the join; the assembled shot still has one source identity and contract. Preserve action state through segment boundaries. Reframing is allowed where the target contract permits it, but accidental generated cuts are defects.

The source audio mix is carried continuously in assembly. Model audio may be retained for diagnosis but does not replace it. Reference audio, audio guides, generated speech and post-generation mouth repair are different capabilities. Input audio cannot be advertised as guaranteed phoneme alignment.

Do not assume an audio output can be disabled without affecting H3's joint computation. Skip unused postprocessing only when the specific workflow supports it. Compare visible dialogue against the original audio before acceptance; evaluate local lip repair only on selected takes that need it, with identity and temporal checks afterward.

## 8. Experiments that earn their cost

After G0 and one complete shot, use six cases: limited-motion dialogue, full-body action, two-character interaction, camera/background motion, effects/occlusion, and a short cut with an essential timed event. Draw them from the user's measured shot inventory.

Choose **at most two conditions** that answer the next important question. Examples: baseline versus source-motion conditioning, or one full-sampling profile versus one acceleration profile. Start with one fixed seed per case: 12 renders maximum. Use a second seed only for uncertain or consequential comparisons, capped at 24 total for this pilot. Stop early when a variant is clearly unusable. Failed runs count toward cost and attempt limits.

Do not cross every strategy with every profile, precision and seed. Paired seed numbers help comparisons within a compatible execution family, but are not a claim of identical noise semantics across models.

Each experiment declares: hypothesis, changed variable(s), fixed inputs, sample selection, contract criteria, budget, early-stop rule, and promotion decision. Report accepted-second yield, cold/warm total time, peak host/VRAM, uncertainty, worst cases and human preference. Score native outputs before optional enhancement.

A 24-shot holdout is a later expansion only if early evidence warrants it. Separate sequences between recipe development and held-out assessment where possible. The purpose is a better policy, not a large benchmark folder.

## 9. Diagnosis before another seed

| Observed failure | Cheap discriminator | Next bounded intervention |
| --- | --- | --- |
| Wrong identity or two characters blended | Inspect bindings, source/target mismatch, actual crops | Correct routing or simplify conflicting identity refs |
| Correct identity, wrong costume/prop | Inspect active appearance/design revision and contract | Bind the correct variant or strengthen one required attribute |
| Source style overcopied | Compare source-motion retention and target style refs | Reduce/remove source video; preserve action as structured text |
| Essential action occurs after the cut | Inspect generated/kept-window mapping and consumed reference | Move beat into the keep window or repair the time map |
| Weak motion or bad endpoints | Check whether those are actually contracted | Test source motion, a guide, or FL2VA only where required |
| Flicker/deformation | Determine repeatable profile issue versus single draw | Profile comparison or one seed control, with a stated hypothesis |
| Apparent frozen frames | Compare intended holds and source style; inspect sequence | Do not reject animation holds automatically |
| OOM or runaway latency | Identify load/encode/denoise/decode phase and actual refs | Requalify memory profile; do not seed-hunt infrastructure failure |
| Poor visible speech | Play selected window against original audio | Local repair/restaging experiment; flag unresolved sync |

Every attempt has one role: baseline, diagnostic control, or repair child. A repair records its parent and changed variables. A seed-only retry is allowed when the hypothesis is stochastic failure, but it consumes the same budget and requires a stopping rule.

## 10. Accept, stop, and expand

Accept a candidate when required constraints have adequate evidence, artistic review accepts it, and it works across neighboring cuts. A good accelerated probe can be the selected output. There is no mandatory “final Base rerender” that risks losing an already accepted take.

Stop exploration when the contract is met, the local budget is exhausted, the next action has low expected benefit, or a missing shared asset is the real blocker. A useful next action may be correcting one character design that affects ten shots rather than rendering a third candidate.

Persist estimates by workload shape: reference tokens/frames, output area/length, execution profile, cold/warm residency, and hardware. Forecast the film from accepted yield and observed shot-duration distribution, including rejected work and model switches. Do not multiply a provider's seconds-per-clip claim by a guessed shot count.

All hosted adapters remain disabled in this plan. Their presence in the historical research is not an operational dependency or a fallback authorization.
