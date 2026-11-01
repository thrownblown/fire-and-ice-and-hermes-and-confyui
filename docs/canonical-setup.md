# FNI canonical setup

THE single source of truth for hardware, network, services, environment, model stores, and
ComfyUI graph doctrine. Everything else (AGENTS.md, Hermes skills, Hermes memory, OptMem)
POINTS here and carries only behavioral rules. If another document disagrees with this one,
this one wins until it is re-verified and edited here.

All facts below verified 2026-10-19 by direct probe (`/system_stats`, `nvidia-smi`,
`tailscale status`, grep of script defaults). LAN subnet is UNSTABLE — DHCP is flapping
between <LAN_SUBNET>/24 and <LAN_SUBNET>/24 (an old router/DHCP server is still alive),
so LAN IPs drift while Tailscale IPs do not. Tailscale is the authoritative rig-to-rig
path. Each section names its verify command —
re-run it before changing a value; never edit from memory.

## 1. Rigs

| | mh370 (the "4090 box") | tombstone (the "5090 box") | goldfishbowl (model-server box) |
|---|---|---|---|
| OS | Windows 11, git-bash/MSYS shell | Ubuntu Linux | Linux |
| GPU | RTX 4090, 24 GB (driver 617.42) | RTX 5090, 32 GB (cudaMallocAsync) | 2x Radeon AI PRO R9700, 64 GB total (ROCm) — reported by goldfishbowl's own STATUS 2026-11-01; not probeable from mh370 |
| RAM | 68 GB | 66 GB | unknown |
| LAN IP | <LAN_IP> (flapping) | <LAN_IP> (flapping) | <LAN_IP> (per goldfishbowl 2026-11-01; was <ROUTER_IP>) |
| Tailscale | <MH370_TS_IP> | <TOMBSTONE_TS_IP> | <GOLDFISHBOWL_TS_IP> · MagicDNS `goldfishbowl` |
| ComfyUI | localhost:8188, v0.40.0 (win32) | :8188, v0.39.0 (linux) — Tailscale <TOMBSTONE_TS_IP>:8188 (preferred) and LAN <LAN_IP>:8188 are the SAME box, two paths; both work from mh370 | none — no `/system_stats` on :8188 |
| Access | local (Hermes sessions run here) | HTTP API ONLY — no SSH, ever. Filesystem visible only via `/view` and the LoRA Manager catalog | HTTP API only — Unsloth Studio :8888, bearer token REQUIRED (no anonymous path); SSH unverified |
| Roles | LM Studio, FNI dev/venv, local ComfyUI (plates, Krea2 probes, restyle) | H3 video renders, Krea2 stills, Qwen-Edit wardrobe runs | Unsloth Studio model server (llama.cpp + ROCm): OpenAI `/v1/chat/completions` + `/v1/models`, Anthropic `/v1/messages` |

Verify: `curl -4 -s http://<addr>:8188/system_stats` — `os: win32` = mh370, `os: linux` =
tombstone; GPU name in `devices[]`. Identity never depends on version numbers or IPs alone.
goldfishbowl has no ComfyUI — identify it with
`curl -4 -s -o /dev/null -w '%{http_code}' http://goldfishbowl:8888/v1/models`: **401 = the server
is up and wants the bearer token** (the key is NOT in this repo or in `~/.hermes/.env` yet — get it
from Alex). A connection-refused there is the server being down, not a bad path.
**Ollama is RETIRED on goldfishbowl (2026-11-01):** `:11434`, `/api/tags`, `/api/ps`,
`/api/generate` and `/api/version` are gone (the service, its health watchdog and the size-guard
proxy are all stopped and disabled). A stale poller gets connection-refused (`curl` exit code /
HTTP 000), which reads like a network fault — it is the migration.

Hard rules:
- The 4090's GPU is ONE shared resource: LM Studio and ComfyUI image-gen are mutually
  exclusive — serialize, never fan out.
- Never an H3 render and LM Studio on the same GPU (H3 stack ~23 GB).
- Jobs run on either rig regardless of type — never assume the rig from the job kind;
  identify the instance (verify command above) when it matters.
- Windows box IPv6 is broken (IPv6-resolving hosts reset with WinError 10054): always `curl -4`.

## 2. Services

- **ComfyUI HTTP API** (both rigs): `/system_stats`, `/queue`, `/prompt`, `/history/<id>`,
  `/view?filename=&subfolder=&type=input|output|temp`, `/upload/image`, `/object_info/<Node>`,
  `/free`. 5090 additionally serves the LoRA Manager at `/loras` (API `/api/lm/`) — the box's
  own inventory of every model file (base_model, Civitai record, trigger words); read it
  before any "does the box have X" question.
- **LM Studio** (mh370 only): OpenAI-compatible at `http://127.0.0.1:1234/v1`; bootstrap CLI
  `C:/Users/gsfny/.lmstudio/bin/lms.exe` (`lms.exe load <id>` / `lms ls`). Models idle-eject;
  an ejected model returns HTTP 400 `"Model is unloaded"` — reload (~35 s for a q4_k_s 8B).
  Roles: vision `qwen3-vl-8b-instruct-abliterated-v2.0` (f16 heavy / q4_k_s light; q4_k_s is
  the FNI_VLM default), embeddings `nomic-embed-text-v1.5`, prompt-craft `sulphur_2`,
  general small `mistral-7b`. Hermes `vision_analyze` also rides this LM Studio.
  The 27B models are crash-prone under delegation and qwq-32b's 40k context is below
  Hermes's 64k floor — subagents use the configured delegation provider, not these.
- **Unsloth Studio** (goldfishbowl only — replaced Ollama 2026-11-01): llama.cpp + ROCm on the
  box's 2x R9700. Endpoints: `http://goldfishbowl:8888/v1` (MagicDNS — PREFER this; the IP can
  move), tailnet `http://<GOLDFISHBOWL_TS_IP>:8888/v1`, LAN `http://<LAN_IP>:8888/v1`. OpenAI
  `/v1/chat/completions` + `/v1/models`, Anthropic `/v1/messages`. **Bearer auth is required**
  (`Authorization: Bearer <key>`) — the old "no auth" property is gone and the key is
  deliberately NOT in any repo: get it from Alex out-of-band.
  - `GET /v1/models` is the inventory AND the residency read: 26 ids, each with `quant`,
    `context_length`/`native_context_length`/`max_context_length`/`vram_fit_context_length`,
    `status`, `loaded`. It replaces `/api/tags` + `/api/ps`. Caveat: one model can appear twice
    (folder name and `:QUANT` variant) — same weights. **Treat this list as authoritative**: the
    id prefix changed once already (`ollama-served/` → `llama-cpp/`, 13 ids) inside a single day.
  - Studio owns residency: request any id and it swaps the runner itself (~15–40 s cold load) and
    evicts after 1 h idle, so mh370 no longer serialises model loads by hand. Batch prompt sets
    per model rather than interleaving arms.
  - Reasoning-capable models run with a capped thinking budget (512 tokens for chat models) plus
    an injected wrap-up nudge, and the trace is not preserved between turns — ask goldfishbowl to
    lift the cap if a comparison cares about the reasoning itself.
  - Port contract for our scripts: read the base URL from `FNI_GF` (default
    `http://goldfishbowl:8888`) and the token from `GOLDFISHBOWL_API_KEY`; never hardcode either.
  - Hermes wiring: provider `goldfishbowl` (config `providers.goldfishbowl`) — base_url now
    `http://goldfishbowl:8888/v1` (set 2026-11-01, verified via `hermes config get`). Still to
    do: the bearer key and the Ollama-era model ids. Appears in the `hermes model` picker under
    Custom Endpoints; also addressable as `custom:goldfishbowl`. Quick-switch aliases
    (`goldfish-70b`, `goldfish-coder`, `goldfish-vision`) all still carry Ollama-style ids.
  - **Breakage from the retirement — mh370 side, NOT yet fixed (2026-11-01):**
    - `providers.goldfishbowl.default_model: qwen3.8-27b-rvn:latest` and the three
      `model.aliases.goldfish-*` ids (`llama3.3-70b:latest`, `terse-coder:latest`,
      `qwen3-vl-32b-heretic:latest`) no longer exist. Replace them with ids read live from
      `/v1/models` (prefix `llama-cpp/`, plus `vllm/...` folder ids).
    - No bearer key in `~/.hermes/.env` (`GOLDFISHBOWL_API_KEY` absent — only DISCORD_BOT_TOKEN,
      LM_API_KEY, OPENROUTER_API_KEY are defined). Until it is added, every goldfishbowl call
      from Hermes or a script returns HTTP 401.
    - 12 first-party files still POST the retired native API (`/api/generate`, `/api/tags`) and
      request Ollama ids — they must be ported to `/v1/chat/completions` with the bearer header:
      `runs/yolo_full_movie.py` (preflight + `BLOCK_MODEL` + its `--endpoint goldfishbowl` pin),
      `runs/diag_yolo_renders.py`, and in `tools/`: `vlm_blocking.py`, `prompt_jury.py`,
      `prompt_fix.py`, `describe_all.py`, `plate_figure_check.py`, `review_scenes.py`,
      `review_sweep.py`, `subhuman_krea2.py`, `log_watcher.py`, `test_hand_fix.py`. (The
      `vlm_*.py` tools that name `qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s` ride mh370's
      LM Studio and are unaffected.)
- **Open WebUI** (mh370 only, added 2026-10-25): chat UI at `http://localhost:8080` (bound
  0.0.0.0, so also `http://<MH370_TS_IP>:8080` over Tailscale), v0.12.4, `WEBUI_AUTH=true` —
  the first account created there becomes admin. **Its model backend is BROKEN (2026-11-01):** the
  launcher (`start-openwebui.cmd` lines 11–14) still sets
  `OLLAMA_BASE_URL(S)=http://<GOLDFISHBOWL_TS_IP>:11434` with `ENABLE_OLLAMA_API=true` and
  `ENABLE_OPENAI_API=false`, so its model list died with Ollama. Fix = re-point it at the Unsloth
  Studio OpenAI endpoint (`OPENAI_API_BASE_URL=http://goldfishbowl:8888/v1`, the bearer key,
  `ENABLE_OPENAI_API=true`, Ollama disabled) — blocked on the same missing key.
  Installed with `uv tool install open-webui` -> `%USERPROFILE%\.local\bin\open-webui.exe`
  (uv-managed Python 3.11.14; does NOT touch `E:\FNI\.venv`). Data/DB
  `C:\Users\<user>\open-webui\data`, launcher `...\start-openwebui.cmd`, log
  `...\logs\open-webui.log`, autostart via Startup-folder `Open WebUI.vbs` (a scheduled task
  was denied — needs elevation). Embeddings run on CPU: no 4090 conflict with ComfyUI/LM
  Studio. Verify: `curl -4 -s http://127.0.0.1:8080/health` -> `{"status":true}`; with a
  token, `GET /ollama/config` currently still returns the DEAD `:11434` URL and its model list is
  empty — that is expected until the re-point above lands, not a separate fault.
- **Hermes dashboard (web admin UI)** (mh370): `hermes dashboard` on `127.0.0.1:9119`
  (loopback by design — auth-gated token/basic login). Tailnet access is via
  `tailscale serve --bg --https=443 http://127.0.0.1:9119` →
  **`https://mh370.tailbd81a6.ts.net/`** (basic auth: `HERMES_DASHBOARD_BASIC_AUTH_USERNAME`
  / `_PASSWORD` in `~/.hermes/.env` — the Hermes home here is `C:\Users\<user>\AppData\Local\hermes`).
  Two gotchas that cost time (2026-10-25): (1) `HERMES_DASHBOARD_PUBLIC_URL` in `.env` MUST
  be the ts.net host (`https://mh370.tailbd81a6.ts.net`) — otherwise tailscale-served
  logins fail `Invalid Host header` (400 on POST /auth/password-login); (2) `tailscale serve`
  must use `--bg` or the config rolls back when the command's session ends (`tailscale
  serve status` reads "No serve config"). Verify from a tailnet node with a real login, not
  just `curl` (loopback curl cannot see it).
- **FNI dashboard (shot browser SPA)** (mh370): static serve of the `E:\FNI` root,
  `python -m http.server 8642 --bind 0.0.0.0 --directory E:\FNI` (plain stdlib, no deps).
  Page: `http://127.0.0.1:8642/browser/index.html` — also `http://<MH370_TS_IP>:8642/browser/index.html`
  over Tailscale and on the LAN. Port 8642 is the standing FNI-dashboard port; serve from the
  REPO ROOT, never `browser/`, because `index.html` carries `<base href="../">` and the page
  fetches `stills/full/` and `refs/` at the root. Verify a relaunch with `curl -4 -sI
  http://<MH370_TS_IP>:8642/browser/index.html` -> 200. Not autostarted: Hermes launches it on
  request as a background terminal process.
- **/history and /queue are memory-only** on both rigs: a reboot wipes them. Output files
  survive on disk; recovery is by name (section 6).

## 3. Environment variables (script contract)

Every FNI script reads these; new scripts MUST too, and must never hardcode addresses:

| var | default | meaning |
|---|---|---|
| `FNI_COMFY` | `http://<TOMBSTONE_TS_IP>:8188` | 5090 ComfyUI (Tailscale) |
| `FNI_PLATE_COMFY` | `http://127.0.0.1:8188` | mh370 local ComfyUI (plates/restyle) |
| `FNI_LM` | `http://127.0.0.1:1234/v1/chat/completions` | LM Studio chat endpoint |
| `FNI_VLM` | `qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s` | vision model id |
| `FNI_STYLE_LORA` | empty = off | style LoRA hook for fullrun graphs |
| `FNI_STYLE_LORA_STRENGTH` | `0.8` | with the above |

Verify: `grep -rn "environ.get(\"FNI_" E:/FNI/pipeline E:/FNI/tools`.

## 4. Python environment (mh370)

- Venv `E:\FNI\.venv` — Python 3.11, uv-managed, **no pip**:
  `VIRTUAL_ENV=E:/FNI/.venv uv pip install <pkg>`. Run everything as
  `.venv/Scripts/python.exe <script>`. System python 3.14 is too new for the wheels — never
  use it for FNI.
- Installed: numpy, faster-whisper, scenedetect, opencv, av, pydantic, pytest, Pillow,
  onnxruntime. **No torch/CLIP** — GPU work happens inside ComfyUI over HTTP, never in-process.
- Scripts in subdirs (`runs/`, `tools/`) that import `fullrun`/`refrun` must
  `sys.path.insert(0, r"E:/FNI/pipeline")` BEFORE the import (bare `import fullrun` from
  `E:/FNI` resolves to the OUTPUT dir as a namespace package). Keep `E:/FNI` on sys.path too
  for `core.*`.
- git-bash path rules: native Windows tools (git, rg, python, curl) do NOT translate
  `/c/...` paths — pass `C:/...` style. `$TMPDIR=/tmp` maps to
  `C:/Users/gsfny/AppData/Local/Temp`. `curl -F` against `E:` paths fails (curl 26) — copy
  uploads to temp first.

## 5. Model stores

- **mh370**: local ComfyUI install `C:\Users\<user>\venvcomfyui\ComfyUI` (launch:
  `python main.py --listen 0.0.0.0 --port 8188 --use-sage-attention`), pulling models via
  `extra_model_paths.yaml` from `E:/comfymodels/` (primary staging store) and
  `E:/stable-diffusion-webui-forge/` (legacy A1111 tree).
- **tombstone**: inventory ONLY through the LoRA Manager catalog and `/view` existence
  probes (200/404). Sort state ledgered in `manifests/lora_sort_5090_moves.jsonl`
  (scheme: `family/base_model` + `kind`; sidecars/previews follow moves).
- Downloads (Civitai): public files need no auth; a gated file returns the HTML login page
  **as HTTP 200** — fetch to `<name>.part`, reject < ~1 MB, verify size/sha256 (and the
  safetensors header `__metadata__.ss_base_model_version`) before landing in a model dir.
  Procedure: comfyui-minimax-h3 skill `references/lora-sourcing.md`.

## 6. Graph doctrine (how ComfyUI graphs are handled — fixed, do not re-derive)

- **Graphs are artifacts, never authored.** They live on disk: `fullrun/graphs/<chunk>.json`
  (production FL2VA), `refrun` equivalents, `runs/T####/` (tests), saved workflow JSONs for
  manual runs. To queue: POST the JSON as-is `{"prompt": <graph>}` to `/prompt`. A returned
  `prompt_id` with empty `node_errors` = ACCEPTED, not finished; completion is
  `/history/<id>` → `status_str`.
- **Every output PNG embeds its exact API graph**: `Image.open(p).info['prompt']`
  (UI graph in `info['workflow']`). "What produced this file?" — models, LoRA strengths,
  seeds, inputs — is a sidecar read, never a reconstruction. Saved mp4s carry the sidecar
  on their workflow PNGs.
- **Never rebuild a graph from memory.** Requeue a `/history` entry (change seed/text only)
  or edit the on-disk graph. The prompt text usually lives in a separate string node wired
  into `prompt`, not the H3 node's own widget. Before first queue of a new graph shape,
  validate model filenames against the TARGET box's `/object_info/<Loader>` — a file on the
  4090 staging disk is not evidence the 5090 has it.
- **Inputs**: `POST /upload/image` (`overwrite=true`) for every file the graph's LoadImage
  nodes name; the render box's `input/` only sees uploaded files.
- **Recovery after reboot**: outputs are named deterministically
  (`<filename_prefix>_00001_.mp4` in `video/`), so probe by name:
  `GET /view?filename=...&subfolder=video&type=output` → 200 survived, 404 lost. Pull with
  `tools/pull_5090.py`; use each history record's OWN `type` field (some artifacts are
  `temp`); always pull workflow sidecar PNGs. Give every chunk a deterministic
  `filename_prefix` up front so recovery is a name-probe pass.
- **VRAM**: low free VRAM + empty queue = a model is still resident. `POST /free`, then
  re-read `/system_stats` — unload is confirmed only on the second read. H3 model swaps are
  manual and only with an empty queue; never script an auto-unload.
- **Queue etiquette**: read `/queue` before posting; throttle batch renders
  (`--max-pending`); leave a running queue alone (it may hold other agents' jobs).

## 7. Outputs and mirrors

- 5090 artifacts are swept to `E:\FNI\renders\5090\`; production renders live in
  `fullrun/output/`, test runs in `runs/T####_<scope>/output/`.
  `renders/workflowtesting/` = manual workflow tests (triage in its `VERDICTS.md`).
- Verify every copy by comparing source and destination COUNTS — never trust the copy
  command's own glob.
- The removable-drive mirror of the render box output uses flat deterministic names; copy
  only what is missing locally.

## 8. Update rule

When reality changes (new rig, moved address, new service, model-store change): re-run the
section's verify command, edit THIS file, and only then touch pointers elsewhere. Skills and
memory hold behavior ("serialize", "never assume the rig", "read the sidecar"); this file
holds ground truth (addresses, versions, paths, defaults). Anything duplicated from here
into another system is a bug — replace it with a pointer.
