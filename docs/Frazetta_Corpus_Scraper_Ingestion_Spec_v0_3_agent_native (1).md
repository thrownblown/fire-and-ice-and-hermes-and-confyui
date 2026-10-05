# Fire & Ice — ReferenceMemory and Corpus Ingestion v0.3

**Revised:** 2026-09-16. **Authority:** [SYSTEM_CONTRACT.md](SYSTEM_CONTRACT.md). This module acquires, identifies and retrieves visual evidence and target references; it does not generate H3 prompts or own a separate project truth store.

## 1. Acquire what a shot needs

ReferenceMemory answers: **Which small set of assets is likely to help this target shot, in these roles, and why?** The goal is useful control coverage per acquisition/enrichment cost, not the largest image count.

Start with the first sequence's characters, location and style needs. Use source frames and approved target designs before crawling. If a role is already covered, a larger corpus has to demonstrate additional value. Missing a useful profile view or environment reference creates a targeted `ReferenceNeed` with affected shots, expected value, search scope and budget.

The old 5,000-image build remains a possible later batch, not the startup task. Initial configurable caps are 50 pages, 200 image downloads and 1 GiB of downloads. Stop sooner when the pilot's roles are adequately covered; exceeding caps requires a new scoped acquisition budget, not a hidden expansion.

## 2. One asset model shared with the film

| Record | Purpose |
| --- | --- |
| `SourcePage` | URL, source identity, fetch time, HTTP/cache metadata, raw snapshot and extracted text |
| `SourceObservation` | Exact page/image relationship and quoted metadata span/locator |
| `Artwork` | Conceptual work or production object, including known variants |
| `Artifact` | Exact bytes, dimensions/media metadata and immutable hash |
| `Derivative` | Normalization, crop, thumbnail, embedding or generated edit linked to parents |
| `AssetAssertion` | Claimed creator, character, production code/type, with method and evidence |
| `ReferenceSelection` | Exact asset/derivative selected for one contract role |
| `ReferenceUsageOutcome` | Observed outcome in a particular renderer/contract context |

These use the canonical SQLite project store. JSONL/Parquet and optional DuckDB views are exports with revision watermarks. A search index is disposable; provenance and source bytes are not.

Artifact byte identity is separate from a painting's identity and a character's identity. Several URLs can yield the same bytes. Several scans, crops, or repaints can refer to one work while remaining distinct retrieval candidates.

## 3. Source priorities retained from research

These are discovery seeds from the supplied research, not a claim that their inventories or image URLs were revalidated in this design pass.

| Priority/source | Initial seed | Intended value |
| --- | --- | --- |
| A: Frazetta Art Museum | [Fire and Ice portfolio](https://www.frazettamuseum.com/products/fire-and-ice-portfolio) | Design drawings and broader Frazetta reference |
| A: Frazetta Girls | [Site](https://www.frazettagirls.com/) | Artwork naming, reproductions and version history |
| A: Bakshi Film Studios | [Fire & Ice project](https://www.bakshistudio.com/projects/fire-%26-ice) | Production objects, characters, sequence/scene/cel metadata |
| A: Gurney Journey | [Backgrounds research lead](https://gurneyjourney.blogspot.com/2015/10/the-backgrounds-for-fire-and-ice.html) | Environment art, palette and production context |
| B: Heritage | [Teegra/Larn production lot](https://comics.ha.com/itm/animation-art/production-cel/fire-and-ice-teegra-and-larn-production-cel-setup-with-key-master-background-by-james-gurney-ralph-bak/a/7375-18456.s) | Production images and dense metadata/timestamp hints |
| C: collector/dealer archives | Discovered for a named gap | Rare alternate views or production material |
| D: community/mirrors | Discovery leads only initially | Find material missing from stronger sources |

Authority is claim-specific. A museum can identify its work; an auction title can still misidentify a character. Source tier never becomes a universal probability that every extracted field is correct.

Start with generic HTML/image extraction and the adapters needed by reachable seeds. Add Shopify/Blogger/auction-specific parsing when it improves yield. Dynamic-page handling is an optional local crawler adapter, not a reason to build a general browser automation platform.

## 4. Acquisition pipeline and restartability

1. Convert a ReferenceNeed into bounded queries and candidate **page URLs**.
2. Normalize URLs conservatively; retain parameters affecting content, signatures or resolution.
3. Fetch/cache page bytes and metadata before extraction.
4. Extract candidate images from HTML, `srcset`, gallery links, metadata and public structured page data.
5. Choose the best accessible artwork candidate within byte/dimension limits.
6. Download to a temporary file, validate media type/decodability, hash exact bytes and publish atomically.
7. Associate every image with source page, image URL, retrieval time and extraction evidence.
8. Normalize, exact-dedupe, propose near-duplicate relationships and extract metadata.
9. Enrich only unique, useful candidates; create role-specific crops and optional embeddings.
10. Evaluate retrieval against actual pilot shots before expanding.

Request state is persisted per URL/fetch revision. Resume successful fetches from cache; retain ETag/Last-Modified and explicit refresh policy. Distinguish a failed fetch from an empty page, parsing failure and page with no useful artwork.

Use per-domain rate limits, bounded retries with jitter for transient failures, Retry-After when supplied, and a failure ledger. Stop repeated retries for authentication/access denial or permanently missing content. Use public accessible assets; do not add login/CAPTCHA bypass. Dynamic rendering does not authorize bypassing a site restriction.

Enforce compressed and decoded size caps, timeouts and redirect limits; reject non-image payloads disguised by extensions. Keep extraction code and fetched text separate so page instructions cannot become executable commands. Keep network crawling outside the GPU worker and pause it if host-memory/I/O pressure threatens rendering.

## 5. Preservation and transforms

Never mutate raw downloads. Each normalized image records parent hash, color/ICC conversion, EXIF orientation, alpha handling, resizing/crop and encoder settings. A derivative may cap its long edge at 6,000 pixels as an initial disk policy; originals remain intact.

RGB conversion alone is not an sRGB color transform. Missing/ambiguous color profiles remain explicit. Preserve aspect ratio and transparency where useful. Do not remove marks or fabricate missing image edges during ingestion; any later creative edit is a separate derivative.

Use resolution, sharpness, cropping, glare, reproduction quality and source context as separate quality dimensions. A rare small production drawing can be more useful than a large irrelevant painting. Minimum dimensions are ranking hints with rare-asset exceptions, not an unconditional 400-by-400 rejection rule.

## 6. Deduplication without erasing information

- SHA-256 equality shares one blob and retains all source observations.
- Perceptual hashes propose near-duplicates. The inherited Hamming-distance threshold of 6 is a calibration candidate, not an automatic merge rule.
- Embeddings can propose related images; a high cosine score does not prove byte or artwork identity.
- Separate `same_work`, `same_version`, `crop_of`, `reproduction_of`, `repaint_of`, and `possible_duplicate`.

Frazetta variants and crops can differ in important identity details. Keep ambiguous relationships unresolved. Select a preferred digital instance **per role and variant**, not one global winner that suppresses a useful detail crop.

Exact duplicates can skip costly processing. Near-duplicates share processing only when the transform and content relationship justify it. Do not embed twenty resizes of the same image by default, but do retain source links and unique variants.

## 7. Metadata with field provenance

Keep page-stated and visually inferred characters/creators/types separately. Metadata extraction precedence is a useful heuristic, not proof: structured metadata, title, description, alt/filename, and model inference can disagree.

Production sequence, scene, cel and drawing codes retain the raw string, parsed value, evidence span and extractor revision. Preserve leading zeros and nonnumeric suffixes. Regex matches are candidates; a timestamp-looking string might be a video-player clock or unrelated number.

Film timestamp hints include display text, parsed rational time, source page, claimed edition if present, and alignment status. They never directly populate the canonical shot timeline. Matching against the user's master belongs to the identity/timeline module.

Use a compact artifact taxonomy: painting, drawing, character/concept design, model sheet, production drawing/cel/background, layout/storyboard, poster/promotion, reproduction, film frame, generated target reference, unknown. Record attribution and production function separately from this taxonomy.

Maintain `rights_basis` as recorded evidence (unknown, provided copy, explicit permission/license reference) and `intended_use` as a separate field (for example visual reference). Downloadability or a source tier does not establish permission. This preserves provenance without turning corpus ingestion into a legal-research project.

## 8. Selective enrichment

Run cheap metadata/dedupe first. VLM enrichment is admitted when a unique asset may satisfy an active ReferenceNeed or improve a canonical design set. Its structured output covers visual subjects, anonymous/candidate identities, bounding boxes, pose, environment, composition, lighting and image quality; every consequential label keeps its method and uncertainty.

Do not ask a VLM to certify authenticity, exact creator, rights or production history from visual style. Unknown is valid. A first-party page claim and model inference remain separate assertions.

Start retrieval with metadata, role filters and human-approved references. Add one pinned image-embedding family if the corpus is large enough to benefit. A second DINO/composition representation is an experiment to address demonstrated ranking failures, not mandatory startup work. Cache by image derivative hash, encoder/preprocessor revision and settings; never mix vectors from incompatible encoders.

Character crops are immutable derivatives with parent, coordinate convention, bounding box/mask and transform. Preserve the original full image as context. A normalized bounding box uses `[x0,y0,x1,y1]` in the parent orientation with strictly positive area.

## 9. Retrieval is role-conditioned selection

Shared roles are `identity`, `face`, `body`, `costume`, `pose`, `action`, `composition`, `environment`, `style`, `palette`, `lighting`, `object`, `motion`, and `audio`. A slot also names its target entity and attributes to preserve. Examples: `identity:teegra`, `environment:firekeep`, `object:larn_sword`.

Apply hard eligibility filters before scoring: role/media compatibility, correct target identity/appearance, approved design status where required, available bytes, and excluded variants. Then compare role relevance, discriminative detail, crop quality, design compatibility, provenance and measured usage context. Keep source evidence and approved target references in distinguishable pools.

Return at most five candidates per requested role initially, with thumbnail, role explanation, score components, provenance, version/variant, prior usage count, uncertainty and known failure associations. Deduplicate near-identical candidates and preserve meaningful diversity. Return “no suitable reference” when appropriate instead of manufacturing a weak winner.

A ReferenceSelection records exact chosen artifact/derivative revision, slot, entity, preserve/avoid attributes, selector, alternatives considered and rationale. It is separate from the search result and immutable once consumed by a render plan. The H3 compiler assigns numerical labels later.

Avoid reference dilution: add a reference only to satisfy a role or test a hypothesis. An identity crop, location reference and concise style specification can be a better first probe than filling every socket. The optimal count is learned from the local renderer, not inferred from its maximum capacity.

## 10. Learn utility without claiming causation

After evaluation, record a ReferenceUsageOutcome with selection/attempt IDs, role, contract/design/profile revisions, quality dimensions, defects, actual cost and whether a controlled comparison isolated the asset. If three references and the prompt changed, no single reference gets credit for the improvement as an established cause.

Retain exposure, selection, success, failure and inconclusive counts. Keep uncertainty and sparsity visible. A frequently selected asset may simply have been shown more often; a selected winner is not an unbiased estimate of all its outcomes.

Initially use explicit scoped heuristics. Propose rules such as “this crop was useful for this character in close-ups under this profile” with supporting and counterexample attempts. Promote only after a useful independent comparison, and reset/revalidate applicability after a design or renderer change.

Exploration is bounded: surface an under-tested eligible alternative when a real reference question warrants an experiment. Do not perform random exploration on every accepted shot or continually expand the corpus because an embedding score is slightly lower.

## 11. Agent operations

Implement the shared `refs.search`, `refs.inspect`, `refs.select` and evidence APIs, plus `refs.explain_rank`, `refs.alternatives`, `refs.needs`, `refs.acquire` and `refs.report_outcome`. Acquisition returns a job with budget and source scope. Selection returns a semantic diff and downstream impact.

A retrieval packet should let the agent decide without reading crawler logs. Those logs remain accessible when provenance or acquisition failure is the issue. Every returned image can be traced back to its page or local source and through every derivative.

## 12. Acceptance and useful reporting

The first slice passes when its required roles have usable selected references; original/source provenance is recoverable; exact duplicates preserve all origins; important variants are not merged; acquisition resumes after interruption; and retrieval can explain an eligible choice or an uncovered need.

The report emphasizes coverage and utility:

- required roles covered, unresolved needs and affected shots;
- useful unique assets per fetch/enrichment budget;
- metadata conflicts and unconfirmed production matches;
- failed/unavailable sources with reason and retry policy;
- retrieval comparisons and rejected misleading references;
- costs saved through cache/dedupe and measured accepted-shot contribution.

Raw counts are diagnostic, not the success criterion. Expand sources, adapters, embeddings and manual cataloging only when they improve these outcomes. Preserve the detailed historical seed queries and source leads in `research_archive/` for targeted reuse.
