# Fire & Ice — Identity, Design and Timeline Specification v0.3

**Revised:** 2026-09-16. **Authority:** [SYSTEM_CONTRACT.md](SYSTEM_CONTRACT.md). This module connects the user's source master, evidence-backed identities, approved remake designs and sequence continuity.

## 1. Establish the user's master, not a presumed edition

The existing local film is the initial `SourceMaster`. Hash it; record selected video/audio streams, presentation timestamps, origins, frame durations, aspect ratio, color characteristics and channel layout. Do not replace it with the 2026 restoration recommended in older research. Another edition is a separate master with an explicit alignment map if it becomes useful later.

Shot detection proposes a segmentation revision. Review fades/dissolves, flashes, held cels, very short cuts and false motion boundaries. A shot ID remains stable through a simple boundary correction; a split/merge creates new shot IDs and ancestry links. All affected evidence/time maps become stale through dependency tracking.

Keep the master intact and make proxies lazily. A source interval can be decoded into a clip when needed; thousands of permanently duplicated high-quality source clips are unnecessary.

## 2. IdentityGraph has three layers

| Layer | Example | Authority |
| --- | --- | --- |
| Source observation | Anonymous track 2 is visible at these exact PTS/regions | Original frames |
| Identity belief | Track 2 is probably Teegra, supported by costume and adjacent confirmed views | Assertions and reviewed evidence |
| Target design | Approved remake Teegra design revision 3 | User/design curation decision |

A source identity correction and a target design change are different mutations with different impact. Generated assets never become evidence of the original film's character identity. Production art can support identity, but its metadata may still be wrong or refer to unused material.

Implement the graph using shared relational records and typed edges. No separate graph database is required. Typical relations are `observed_in`, `depicts`, `identified_as`, `variant_of`, `mentioned_by`, `spoken_by`, `matched_to_frame`, `derived_from` and `approved_target_for`.

## 3. Seed inventory, not populated ground truth

The supplied research identifies the following useful starting entities. These are seed labels and discovery targets; no appearances or timestamps have been verified against the user's actual copy in this revision.

| Entity | Initial handling |
| --- | --- |
| Larn, Teegra, Darkwolf, Nekron | Lead design/identity candidates; prioritize those in the first sequence |
| Juliana, Jarol, Taro, Roleil, Otwa, Tutor | Named supporting candidates; curate when needed |
| Monga, Pako | Credited names with unresolved visible mappings; retain unresolved |
| Envoy, Defender Captain | Role labels until individual identity is established |
| Subhuman groups | Group taxonomy plus persistent individual tracks/design instances |
| Dragonhawks, giant octopus, giant swamp lizard | Creature entities with distinct design and motion needs |
| Shaitan | Name reported in subtitle research; identity/type requires source verification |

Keep cast credits, visual/rotoscope performers and voice performers in different fields. The supplied research's [AFI lead](https://catalog.afi.com/Film/57961-FIRE-AND-ICE) and complete credit table remain in the historical source document; they do not automatically label visible people.

Retain aliases with their sources. The research reports `Roleil`/`Roliel` and `Agatar`/`Akatar`; ingestion preserves the original string and a separately resolved canonical entity. Do not overwrite source text during normalization.

## 4. Text, voice and visibility are separate

For each cue store: original text/source, original start/end, speaker if known, mentioned entities, aligned master interval, alignment method/revision, uncertainty and supporting anchor points. A name being spoken does not prove that character is visible; visible mouth motion does not alone prove the audible speaker.

Alignment procedure:

1. Import local subtitles when available; otherwise use retrieved text as a provisional source.
2. Compare multiple anchor points across the relevant interval. Test a fixed offset before rate correction; use piecewise mappings only when measured drift or edits require them.
3. Preserve residual errors and unresolved segments. Do not apply a global FPS conversion because a subtitle release label suggests one.
4. Obtain current/preceding/following dialogue by interval queries over the shared cue records, rather than copying mutable text into every shot row.
5. Validate cross-cut lines against the continuous audio track and assign visible/offscreen speech independently.

The production screenplay has not been supplied. The old research did not establish an authoritative open screenplay. A web transcript remains a transcript; missing action text must not be fabricated to fill that gap.

## 5. External timestamp and production-code leads

The following inherited leads are valuable search windows, not master coordinates:

| Research lead | How to use it |
| --- | --- |
| Teegra/Larn production setup near 34:41 | Search a broad interval; match actual composition and confirm a frame |
| Larn/Roleil production setup near 51:11 | Cross-check production image, dialogue and the user's master |
| Teegra `AB / 3 / 53` | Store sequence/scene/cel as strings and attach the original page claim |
| Larn/Teegra `Z / 4 / 51` | Keep a candidate archival-to-film relation pending a visual match |
| Nekron `FA / 25 / 49` | Same; production sequence order is not assumed to equal final edit order |

Source leads include the [Teegra/Larn Heritage lot](https://comics.ha.com/itm/animation-art/production-cel/fire-and-ice-teegra-and-larn-production-cel-setup-with-key-master-background-by-james-gurney-ralph-bak/a/7375-18456.s) and [Bakshi Teegra page](https://www.bakshistudio.com/product-page/princess-teegra-shielding-herself), inherited from the supplied research rather than revalidated here. Detailed dialogue intervals, production sources and unresolved mappings remain in the archive.

An embedding/perceptual match produces a candidate. Confirmation records the image, exact master frame/PTS, crop/transform, method, reviewer or calibrated verifier, and alternative matches. A production cel can span multiple frames, and backgrounds can recur; retain one-to-many relationships.

## 6. Design sets for the remake

For each needed lead, present a compact design decision packet: source identity evidence, selected production/style references, candidate target images, differences from source, and intended invariant attributes. The user curates the target design; the agent can prepare views using existing compatible local image/edit models and LoRAs.

Record the complete generation recipe for generated assets: base-model and LoRA hashes/compatibility, prompt, seed, edit masks, input revisions, workflow and manual changes where known. An imported manually edited image is valid even without full generation provenance; mark that gap rather than inventing parameters.

Start with the smallest useful reference set, often a clean identity/body view and an additional discriminative angle. Add face, profile, rear view, expression, weapon detail or silhouette only when a shot needs them. Do not require a full turnaround/T-pose collage for every character.

Each reference declares supported roles and limitations. A collage can cause duplicate characters or ambiguous identity; retain separate crop/view alternatives. A dramatic lighting reference may be excellent for style but poor for identity. The approved design includes stable distinguishing attributes and acceptable appearance variations.

Design lifecycle is `draft → reviewed → approved → superseded`. Approval identifies the actor and decision revision. Existing approved designs can be used autonomously within scope; routine rendering does not re-request approval. A new global design revision has an impact preview listing affected shots and estimated rework.

## 7. Stable identity, appearance state and illumination

Keep three concerns separate:

- **Stable target identity:** face structure, characteristic hair/costume/silhouette and other approved discriminators.
- **Appearance state:** costume version, injury, wetness, dirt, held props, alive/dead or transformed state, with justified temporal applicability.
- **Render context:** lighting, camera distance, pose and occlusion.

Lighting should not create a new canonical character by default. A materially different state can require a new reference derivative, still linked to the same identity. Appearance intervals can be discontinuous; use explicit sequence/shot applicability and evidence rather than assuming every shot between two numbers shares the state.

Human identity corrections preserve competing prior assertions, explain their basis and invalidate only consumers of the changed view. Previously selected takes stay visible but require re-evaluation when the correction affects them.

## 8. Locations, props and extras are continuity assets too

A location has source evidence, canonical identity, aliases, approved target design, palette/lighting families, recognizable landmarks, and optional staging relationships. It can have several camera-ready references without pretending to be a complete 3D scene. Environment identity and composition-anchor roles remain distinct.

Give important props stable IDs and state/ownership transitions. A sword appearing in the wrong hand can matter more than a minor camera mismatch. Tie those constraints to story and neighboring cuts.

Generate extras from scoped faction/sequence design rules after leads and locations are stable. Assign persistent target instance IDs and deterministic recipe seeds; reuse them across adjacent shots. A different camera view must not regenerate a new person accidentally. Source-unknown tracks can map to approved new extra designs without falsely naming them Monga or Pako.

## 9. Sequence continuity contract

For each short sequence, persist:

- story entry/exit state and required event order;
- characters and approved design/appearance revisions;
- location/prop ownership and essential spatial relations;
- audio interval, cross-cut dialogue and visible/offscreen speaking;
- shot boundary obligations such as direction, eyeline, pose, prop hand and motion continuation;
- style/palette constraints and permitted staging freedoms.

Before selection, review each candidate with immediate neighbors and original audio. When an upstream selection changes, recheck only edges that consumed its boundary state. Do not propagate an accidental generated prop or costume error into subsequent contracts merely because it appeared in the chosen frame.

A source mismatch is allowed where the target contract permits it. A contradiction within the newly staged sequence is still a defect. This is why independent per-shot quality scores cannot establish film-level coherence.

## 10. Agent interfaces and review ergonomics

Identity/context reads return the relevant identity view, evidence thumbnails, competing claims, current design/appearance revision, local continuity obligations and useful reference options. Default to the selected shot/sequence, not the full cast database.

Review requests are narrow: “Which of these two source tracks is Taro?” or “Keep the approved design despite this occluded source view?” Include the frames and downstream impact. A low-impact unresolved extra can remain anonymous; a lead identity conflict blocks the affected render.

Record human decisions as structured evidence/target choices. Do not bury them in chat history. The next agent should recover the result through `project.resume` and `belief.explain` without replaying a conversation.

## 11. Initial implementation and acceptance

The first slice needs only the user's master, corrected boundaries for a short sequence, needed cue alignment, a few confirmed identities, approved lead/location designs, and continuity edges. A complete cast atlas or reconstructed production inventory is not a prerequisite.

Acceptance requires:

- exact source frames/PTS are recoverable from every identity assertion;
- mentions, speakers and visual presence remain independent;
- no inherited Internet timestamp is treated as confirmed master time;
- unresolved aliases/identities survive without forced guesses;
- source identity and target designs can change independently with traceable impact;
- adjacent shots reuse correct target identities/appearance states;
- continuous original audio remains aligned across cuts;
- a correction makes only the proper derived work stale and never deletes historical evidence.

Keep a small set of confirmed and deliberately ambiguous identity examples for calibration. Split evaluation by sequence where possible, and do not count model agreement as ground truth.
