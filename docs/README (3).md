# Fire & Ice — Coherent Local System Design v0.3

**2026-09-16 · Ubuntu · one RTX 5090 · 64 GB RAM**

The five supplied design documents have been rewritten around one operating loop: understand evidence, state the creative target, choose controls, run a bounded local experiment, judge it in the film, and preserve what was learned.

Start with [Ref2V_AI_Project_Brainstorming.md](Ref2V_AI_Project_Brainstorming.md), which is now the project architecture and decision document. Then read [SYSTEM_CONTRACT.md](SYSTEM_CONTRACT.md) and [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).

| Specification | Purpose |
| --- | --- |
| [H3_Render_Strategy_v0_3_agent_native.md](H3_Render_Strategy_v0_3_agent_native.md) | Local feasibility, profiles, timing, probe/repair policy |
| [VLM_H3_Prompting_v0_3_agent_native.md](VLM_H3_Prompting_v0_3_agent_native.md) | Evidence, uncertainty, semantic planning and exact compilation |
| [Fire_and_Ice_Character_Timeline_v0_3_agent_native.md](Fire_and_Ice_Character_Timeline_v0_3_agent_native.md) | Source identity, approved designs, audio alignment and continuity |
| [Frazetta_Corpus_Scraper_Ingestion_Spec_v0_3_agent_native.md](Frazetta_Corpus_Scraper_Ingestion_Spec_v0_3_agent_native.md) | Targeted acquisition, provenance and contextual reference retrieval |
| [CHANGE_RECORD.md](CHANGE_RECORD.md) | Decisions, corrections, evidence status and migration |

The complete package also includes:

- [contracts/fi_core.schema.json](contracts/fi_core.schema.json): minimal machine-readable core records;
- [examples/probe_cycle.json](examples/probe_cycle.json): a wholly synthetic linked example;
- [config/bootstrap_policy.yaml](config/bootstrap_policy.yaml): explicit editable startup limits;
- [validation/validate_bundle.py](validation/validate_bundle.py) and [validation/REPORT.md](validation/REPORT.md): package checks and results;
- `research_archive/`: unchanged copies of all five inputs, preserving detailed source leads and historical reasoning.

The first build milestone is one real local shot, followed by a coherent three-to-five-shot sequence with original audio. Hardware performance and generated-video quality remain to be measured. This package is the design and contract foundation, not the completed application.
