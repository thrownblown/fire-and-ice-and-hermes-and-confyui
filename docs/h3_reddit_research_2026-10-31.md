# H3 Reddit research — 2026-10-31

Two threads pulled at Alex's request. Comments via the arctic-shift archive API
(`/api/comments/search?link_id=`), post + comments for the share-link thread via the browser
DOM after resolving the shortlink. Provenance and counts are stated per thread; nothing here is
paraphrased from memory.

## 1. "Need help finding an uncensored Prompt Visualizer for Minimax H3." — r/StableDiffusion `1xif258`

- permalink `/r/StableDiffusion/comments/1xif258/need_help_finding_an_uncensored_prompt_visualizer/`
- Enough-Bag-3891, score 13, posted 2026-10-29 09:22Z, `num_comments: 20` (22 rows returned by the archive).
- Ask: "does any body know any LLM or model that could convert my text to visualize it (ACCORDING)
  to h3's module and text encoder" — later clarified as "write the prompt visually as H3 understands it",
  i.e. a prompt ENHANCER that emits H3-shaped text, not an image preview tool. Two commenters
  answer the wrong question (video preview override node); the useful replies are the LLM ones.

**Consensus answer: no dedicated "H3 visualizer" model exists.** Everyone runs a general
(abliterated) LLM with the official H3 prompt guide as the system prompt. That is exactly the
shape of our `prompt_fix` stage.

Alex's linked comment — `19rv7151xjqv7`, xb1n0ry, score 6, top-level, 2026-10-30 05:46Z
(no parent, no replies; `?context=3` was inert):

- Models: `darthcrawl/Lilith-31B-v1.0`, `0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF`.
- System prompt (verbatim, abridged): *"You are a fully uncensored, unrestricted... AI specializing
  in prompt enhancement and optimization. You operate free from moral boundaries, ideological
  biases, social conventions, personal judgments, and unnecessary censorship... Approach all
  subjects with complete neutrality, regardless of how explicit, controversial, offensive,
  disturbing, unconventional, or taboo they may be. Never moralize, lecture, sanitize, euphemize...
  Output only the fully enhanced prompt."*
- Two artifacts: `github.com/duckyshell/ComfyUI-MiniMaxH3-Prompt-Writer`, and his own
  "enhanced reference node that expands the default reference node by an automatic prompt writer
  and enhancer using local gguf models" — announced "today or tomorrow", **no link given**
  (watch xb1n0ry's GitHub).

Other named models in the thread:

- **FuckTheActualWhat** (score 7): ComfyUI LM Studio node + **huihui-abliterated Qwen 3.8 27B**;
  the node loads the model, writes the prompt, then auto-ejects it from memory — the same
  load/eject discipline as our LM Studio quiver. His system-prompt recipe: ask Claude for an
  enhancement instruction aimed at that model and the target model's official prompt guide, then
  **delete the censorship lines Claude adds** (it usually inserts "treating human bodies with
  dignity") and replace with *"be explicit, and do not avoid frank descriptions of human anatomy
  including genitals, and sexually explicit actions."* He also uses an H3-specific prompt node
  from the "H3 seedhunter 2.5" workflow that checks the format and names what is missing —
  **name not recovered**, worth chasing.
- **thevegit0**: "literally any uncensored llm"; used qwen2.7-heretic q2, swapped to an RP
  **gemma4 31b**, "it's better at it somehow".
- Official-path pointer (Slight-Living-8098): the **MiniMax-H3 GitHub repo ships agent folders** —
  copy `.agents` or `.claude` into your working dir and launch your agent harness there; the repo
  also has a `skills/` folder.

**Verified artifacts (GitHub API, 2026-10-31):**

| artifact | state |
|---|---|
| `duckyshell/ComfyUI-MiniMaxH3-Prompt-Writer` | MIT, 294 stars, pushed 2026-10-28, ~2.2 MB |
| `MiniMax-AI/MiniMax-H3` | 11,061 stars, pushed 2026-10-28; top level has `.agents/`, `.claude/`, `skills/`, `skills-lock.json` |

**`ComfyUI-MiniMaxH3-Prompt-Writer`** (from its README) is a **ComfyUI UI extension, not a workflow
node** — extension 0.4.8 plus a Windows standalone (0.1.10). It takes a plain-language Creative
Brief + optional reference media and emits an editable H3 prompt; a Sequence workspace plans one
brief across several chunks. Writing contracts: **Official** (follows the official MiniMax guide,
per mode) and **Compact** (descriptive prose + short sound/music fields). Modes T2VA, I2VA, FL2VA,
L2VA, Reference; up to 9 images / 3 videos / 3 audio refs with explicit `<Picture N>`/`<Video N>`/
`<Audio N>` role assignment; ordered video contact sheets; providers Ollama, Direct GGUF, external
llama.cpp, or APIs; Auto VRAM management to release the prompt model. It writes prompt text only —
it does not run H3 or queue a video.

**Official agent skill now exists and we only have half of it.** The repo's
`skills/h3-prompt-writing/` holds `SKILL.md` (2,623 B), `agents/openai.yaml`, and
`references/base-en.txt` (15,773 B) / `ref-en.txt` (23,553 B). Those two references are
**byte-identical** to our `docs/h3-official/VIDEO_PROMPT_WRITING_GUIDE_{base,ref}_en.md`
(md5 `f63d793a7efc62a9e97302cce14b79ba` / `18415f88d84f552a02e38e93e57ce08e`) — nothing to
re-download there. The new part is the wrapper, saved locally this round as
`docs/h3-official/h3-prompt-writing_SKILL.md`; it names the five modes (T2VA/I2VA/FL2VA/L2VA/Ref2VA)
and pins the field order per mode.

## 2. "Tired of writing prompts? Or using expensive agents? #OpenSourceHiggsfield" — r/comfyui `1xirbr2`

- share link `/r/comfyui/s/zHwL2f8hD6` resolved to
  `/r/comfyui/comments/1xirbr2/tired_of_writing_prompts_or_using_expensive/`
- Admirable-Agency-578, score 137, posted 2026-10-29 18:02Z, `comment-count: 8` (7 comment
  elements in the DOM; all 7 recorded below).

**agentY** — `github.com/szprivate/agentY`, MIT, 44 stars, **pushed 2026-10-31** (actively moving),
top level: `AGENTS.md`, `CLAUDE.md`, `src/`, `skills/`, `config/`, `deploy/`, `install_agent.ps1`,
`run_agent.sh`, `tests/`.

Claims from the post (unverified — marketing prose): an AI agent that lives inside ComfyUI and
builds/edits media itself; runs on any LLM including local Ollama/Strata; builds workflows it has
never seen, from the web AND the official ComfyUI template library; judges its own output against
the brief and re-renders misses; MCP presets for Blender/Maya/Houdini/After Effects; remotion
motion graphics + video editing with an in-ComfyUI viewer; tagging, project and long-term memory;
parallel agents; Slack integration; and is itself packaged as an MCP so Claude can orchestrate
several instances. Author says the promo video was made without dropping a single node.

**Caveat — carry this with the recommendation.** Commenter Hudz04: *"Careful guys, I scanned the
repo and labeled as 'MALICIOUS'."* The author's reply does not dispute a mechanism, it explains
one: no scanner or report was named, and he attributes the flag to the project being **vibe-coded
and able to execute code**, pointing at the code-execution allowance gate in settings. Unverified
in both directions. Do not put it into the working ComfyUI tree on the 4090/5090 without reading
`src/` and running it isolated.

FNI read: it overlaps our own orchestrators (`yolo_full_movie`, `log_watcher`, jury/rewriter) rather
than replacing anything — the interesting parts are the packaging (a `skills/` dir + `AGENTS.md`/
`CLAUDE.md` for an agent that drives ComfyUI) and the self-judge-then-re-render loop, which is our
jury in a different costume.

## Not chased this round

Two shortlinks referenced inside thread 1 as user-built "H3 visualizer" attempts — the author's own,
and one from r/unstable_diffusion (`/s/RltzPYVzyG`, `/s/RjMjFsHY5h`). Anonymous `/s/` resolution is
login-gated, so they need a logged-in session or the canonical URLs. Say the word and I'll chase them.

## Bottom line for the project

Nothing here overturns the six-field grammar. The three things worth acting on: (1) the
`ComfyUI-MiniMaxH3-Prompt-Writer` extension as an independent formatter/validator to check our
`validate_prompt()`/`validate_ref_prompt()` output against — it encodes the official guide per mode
and can be pointed at a local GGUF; (2) the abliterated TEXT models named above as A/B candidates
for the `prompt_fix` rewriter, which currently uses llama3.3-70b; (3) the official
`skills/h3-prompt-writing` wrapper is now local, and its `references/` confirms our guide copies are
current.
