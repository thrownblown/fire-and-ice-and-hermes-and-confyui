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
  `/v1/chat/completions` + `/v1/models`, Anthropic `/v1/messages`. **Bearer auth is required** and
  it wants a JWT-class token: `Authorization: Bearer <token>`, where `<token>` comes from
  `POST /api/auth/login` (`{username,password}` — the Studio's owner account, `default_username:
  unsloth`) or from an API key minted at `POST /api/auth/api-keys` (`{name, expires_in_days}`,
  response `{"key": ...}` shown once). Keys/tokens are NEVER in a repo — get them from Alex
  out-of-band.
  - **Two distinct 401 bodies are the diagnostic** (both `authentication_error`):
    `"Not authenticated"` = no usable `Authorization` header reached the auth layer (also what you
    get if you use `X-Api-Key` / `api-key` — those header names are IGNORED). `"Invalid token
    payload"` = the header was read but the string is not a decodable token. **Any non-JWT string
    produces the second one**, including a random one, so `"Invalid token payload"` tells you the
    string is the wrong KIND of artifact — it does not mean "wrong key, close enough".
  - Alternative sanctioned mode: `GET/PUT /api/settings/keyless-api-access`
    (`scope: off|inference|full`, `tools`, `exposure: colab|public_url|private_lan|network`).
    `scope=inference` + `exposure=private_lan` would let the tailnet use `/v1` with no key at all —
    a one-time owner-authenticated setting, Alex's call, not ours to flip.
  - Full spec is public on the box: `curl -4 -s http://goldfishbowl:8888/openapi.json`
    (Unsloth UI Backend, v2026.10.11, 583 paths, `HTTPBearer` scheme). `/api/health`, `/docs`,
    `/openapi.json`, `/api/auth/status`, `/api/auth/identity` answer UNauthenticated.
  - `GET /v1/models` is the inventory AND the residency read: 26 ids, each with `quant`,
    `context_length`/`native_context_length`/`max_context_length`/`vram_fit_context_length`,
    `status`, `loaded`. It replaces `/api/tags` + `/api/ps`. Caveat: one model can appear twice
    (folder name and `:QUANT` variant) — same weights. **Treat this list as authoritative**: the
    id prefix changed once already (`ollama-served/` → `llama-cpp/`, 13 ids) inside a single day.
  - Studio owns residency: request any id and it swaps the runner itself and evicts after ~1 h
    idle, so mh370 no longer serialises model loads by hand. **But it is a LOCAL CONSUMER MACHINE,
    not a datacentre: a model switch takes MINUTES, not seconds** (measured and stated by Alex
    2026-11-04 — earlier "~15–40 s" figures were optimistic). Consequences that have each cost a
    session:
    - **The first message after a switch pays the whole load.** Do not read a slow or failing first
      call as a broken model/endpoint: `core/gf_client.py` defaults to a 900 s timeout on purpose,
      and a retry loop that gives up in 60 s will "prove" a fault that is just a cold runner. Wait
      it out, or check `GET /v1/models` → `loaded` first and budget accordingly.
    - **Never evict needlessly.** Every probe of a DIFFERENT id unloads the resident one and costs
      minutes to bring back — so a one-off "control" call against another model is not free: it
      evicts the model you were testing and can invalidate your own diagnosis (an image call that
      failed cold can look exactly like a broken vision projector). Check `loaded` before probing;
      if the model you need is resident, test THAT one and leave the others alone.
    - Batch prompt sets per model rather than interleaving arms (juror phases, not per-chunk
      rotation) — the per-switch cost is what makes interleaving pathological.
  - **There is NO thinking cap on our arms** (goldfishbowl verified it from the running process,
    2026-11-01 — the earlier "512-token cap" note describes their server-side defaults, not our
    models). The real hazard is the OUTPUT allowance: the abliterated arm thinks without a budget,
    so a small `max_tokens` is spent entirely on reasoning and the API returns a **400 whose body
    reads like prose** ("The model used its whole output allowance of N tokens on reasoning…") —
    it looks like the model failed and it is a token-budget artifact. Use `max_tokens >= 2048`
    (ideally 4096) on that arm. The control cannot think, so a small budget handicaps exactly one
    arm and silently corrupts the comparison.
  - **A 200 is not proof the model exists.** An UNKNOWN model id returns HTTP 200 served by
    whatever is RESIDENT. Always check that the response's `model` field equals the id you asked
    for before building a run on it.
  - **Verified servable 2026-11-01** (response `model` field checked on both): `llama-cpp/qwen3-vl-8b-abl_latest`
    (5 s, answered "PONG") and `llama-cpp/huihui_ai_Qwen3.8-abliterated_27b` (15 s cold, answered a
    rewrite with `finish_reason: stop` at `max_tokens: 2048`). The A/B arm therefore works with the
    documented settings. Not yet exercised: the control `llama3.3-70b` (48.7 GB, saturates both
    cards — load it only for the run itself).
  - **Prompt overhead is real:** a 6-word user message billed `prompt_tokens` 1290–1499, i.e. the
    server injects ~1.3k tokens of its own template per call. Budget for it when comparing arms,
    and never read `prompt_tokens` as our prompt's length.
  - Residency: the control (`llama3.3-70b`) saturates BOTH R9700s (31.8 + 32.3 GB of 64 GB) —
    run that arm alone, nothing else resident beside it.
  - Port contract for our scripts: read the base URL from `FNI_GF` (default
    `http://goldfishbowl:8888`) and the token from `GOLDFISHBOWL_API_KEY`; never hardcode either.
  - Hermes wiring: provider `goldfishbowl` (config `providers.goldfishbowl`) — base_url
    `http://goldfishbowl:8888/v1`, `key_env: GOLDFISHBOWL_API_KEY`, `default_model:
    RVN-Q8_0-mtp` (2026-11-01, verified via `hermes config get`). Appears in the `hermes model`
    picker under Custom Endpoints; also addressable as `custom:goldfishbowl`. Quick-switch aliases
    now on live ids: `goldfish-70b` → `llama-cpp/llama3.3-70b_latest`, `goldfish-coder` →
    `llama-cpp/qwen3-coder_30b`, `goldfish-vision` → `llama-cpp/qwen3-vl-32b-heretic_ctx128k`
    (all four strings were checked against goldfishbowl's published 22-id snapshot,
    `agents/goldfishbowl/STATUS.md` → "Served models"). Still to do: the bearer key.
  - **SERVABILITY RULE (goldfishbowl's, and it bites):** the listing is not proof a model
    LOADS. Confirm a model actually answers before building a run on it — `vllm/qwen3.8-27b-heretic`
    sat in the list as an incomplete download and is NOT servable.
  - **A VLM can be listed, `loaded=True`, answer TEXT — and fail every IMAGE (seen 2026-11-04,
    root-caused by goldfishbowl).** It was NOT the vision projector: the mmproj was present and
    loaded (`has vision encoder`, `loaded multimodal model '.../mmproj-qwen3-vl-32b-heretic_ctx128k.gguf'`).
    It was a **VRAM budget failure that is SILENT at load**: the 32B was served at `n_ctx = 106496`,
    whose KV cache alone committed 26,624 MiB (ROCm0 13,728 + ROCm1 12,896) on top of 32,410 MiB of
    weights — ~59.5 GB of 64 GB. The vision warmup (`get_dummy_batch: warmup with image size =
    1472 x 1472`) then failed to allocate 418 MiB (`cudaMalloc failed: out of memory`), and
    **llama.cpp logs that OOM and carries on**, reaching `loaded multimodal model` with a dead
    vision graph. Symptom from the client side: text answers normally, every image returns HTTP 500,
    and the body differs by which way it degraded — `Could not reach an upstream service` = an
    instance that degraded at load (Studio retries the load ~9×, which looks like a connection
    outage window from here), `failed to process mtmd chunk` = an instance that loaded but could not
    allocate mtmd buffers for a real image. **Fix was server-side: `max_seq_length` → 32768 on that
    model's override** (KV 26,624 → 8,192 MiB, ~18 GB freed) — verified with a real image, not a
    status code.
    - **Consequences for us:** the 32B's window has moved twice — 106,496 → 32,768 (the VRAM fix above)
      → **65,536 (CURRENT; raised 2026-11-05 and verified in the load log: `n_ctx = 65536`, KV
      16,384 MiB, zero `cudaMalloc failed`, with a real 1472x1472 image and a three-image call at
      7,695 prompt tokens).** An image COSTS CONTEXT as well as VRAM (~4k tokens for a max-size plate),
      so at 65,536 several plates in one call are comfortable; keep sending ≤1024 px JPEGs.
    - **Tool support is per-model, and it was verified by probe rather than by template text**
      (goldfishbowl sent a real `tools` array): `qwen3.8-27b-reasoning-medium-q6` and
      `qwen3-8b-vision-small` return real tool_calls, while **`Cydonia-24B-v4r-Q8_0`,
      `Qwen3.8-27B-OBLITERATED` and `Qwen3.8-Flash-Next-…/IQ3_XXS` do NOT advertise tools.** Any
      client that always sends `tools` — Open WebUI does — gets a 400 on those three, and that error
      is about the MODEL, not the client and not the endpoint.
    - **Diagnostic order when a VLM returns 500 on images:** (1) check `loaded` in `GET /v1/models`;
      (2) reproduce with your OWN client (text vs image — a text 200 + image 500 localises it to the
      vision path); (3) **ask the box's owner for the LOAD LOG before theorising** — the OOM above is
      invisible from outside, and a guess about mmproj/mtmd workers is exactly the guess that was
      wrong here. Symptom from the client is never enough to name the cause.
  - **Breakage from the retirement — mh370 side, NOT yet fixed (2026-11-01):**
    - ~~`providers.goldfishbowl.default_model` + the three `model.aliases.goldfish-*` ids carried
      Ollama-era names~~ **FIXED 2026-11-01** from goldfishbowl's published live list:
      `RVN-Q8_0-mtp` (their source-name form of the retired `qwen3.8-27b-rvn:latest` — same
      weights), `llama-cpp/llama3.3-70b_latest`, `llama-cpp/qwen3-coder_30b`,
      `llama-cpp/qwen3-vl-32b-heretic_ctx128k`. All four appear in the snapshot; NONE has been
      confirmed to answer yet (see the servability rule above) — that needs the key.
      Note the dedupe that came with the list: `llama-cpp/cydonia-24b_q8_0`,
      `llama-cpp/qwen3.8-27b-rvn_q6` and `llama-cpp/qwen3.8-27b-rvn_latest` were REMOVED
      (duplicates of the source GGUFs, kept as `RVN-Q6_K-mtp` / `RVN-Q8_0-mtp` / `RVN-BF16-mtp`).
    - **Key: RESOLVED and verified 2026-11-01.** The string first supplied was
      `ADMIN_PASSWORD.txt`, the Studio UI's BROWSER login password (sending it returns 401
      `"Invalid token payload"`, byte-identical to a random string). The correct artifact is an
      **API key: `sk-unsloth-` prefix, 43 chars, plain bearer token** (not a JWT, not
      session-bound, works from any host). goldfishbowl minted one labelled `mh370` at
      `~/.unsloth/studio/MH370_KEY.txt` (0600) on their box; Alex handed the value over and it is
      now in `~/.hermes/.env` as `GOLDFISHBOWL_API_KEY`. Verified from mh370 the same minute:
      `GET /v1/models` → **200, 22 ids**, matching goldfishbowl's published snapshot exactly, and
      all five ids we hold are present. Inference confirmed on two ids with the response `model`
      field checked (see below). No Hermes restart was needed — `key_env` is read per call.
    - **PORT COMPLETE 2026-11-05** (this bullet used to be "12 first-party files still POST the
      retired native API"). All twelve are off `:11434` and now go through `core/gf_client.py`:
      `runs/yolo_full_movie.py` (preflight + `BLOCK_MODEL` + its `--endpoint goldfishbowl` pin),
      `runs/diag_yolo_renders.py`, and in `tools/`: `vlm_blocking.py`, `prompt_jury.py`,
      `prompt_fix.py`, `describe_all.py`, `plate_figure_check.py`, `review_scenes.py`,
      `review_sweep.py`, `subhuman_krea2.py`, `log_watcher.py`, `test_hand_fix.py`. Verified: all
      compile + import, and a live alias call returns `PONG` with the response's `model` field
      checked. No live `:11434` literal remains in code (only docstring prose that records the
      retirement). (The `vlm_*.py` tools that name `qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s`
      ride mh370's LM Studio and were never affected.)
    - **Name the ALIAS, not the id.** goldfishbowl published 24 friendly aliases (2026-11-05) that
      resolve at the edge; `core/gf_client.py` holds the alias→id table (`ALIASES`) and resolves
      *before* the request, so `strict_model` still verifies which model actually answered (an alias
      request echoes the RESOLVED id, so comparing against the alias would fail a good answer).
      Tools now name `qwen3-32b-vision-large`, `qwen3-8b-vision-small`, `qwen3-coder-30b`,
      `llama3.3-70b-chat-xlarge`, `magnum-72b-rp-xlarge`. The id prefix has already moved twice in
      one day (`ollama-served/` → `llama-cpp/`), and a rename moves every id under it — with the
      table, the next rename is one dict entry. The **full 24-row table is now encoded** in
      `gf_client.ALIASES` (published in agent-coord `agents/mh370/INBOX.md`; authoritative copy
      `~/models/CATALOG.md` on that box) and every entry was verified against the live `/v1/models`
      list — all 24 targets exist. `qwen3.5-35b-chat-large` closes prompt_jury's raw-id gap. One
      caveat carried with the table: `magnum-v4-72b` declares native 32,768 while the VRAM fitter
      serves it at 177,408 cells — do not use it for long context.
- **Open WebUI** (mh370 only, added 2026-10-25): chat UI at `http://localhost:8080` (bound
  0.0.0.0, so also `http://<MH370_TS_IP>:8080` over Tailscale), v0.12.4, `WEBUI_AUTH=true` —
  the first account created there becomes admin. **Re-pointed 2026-11-01 and the re-point LANDED:**
  the launcher now sets `OPENAI_API_BASE_URL(S)=http://goldfishbowl:8888/v1`, `ENABLE_OPENAI_API=true`,
  `ENABLE_OLLAMA_API=false` with the key read from the Hermes `.env`, and the running instance
  (started 2026-11-03, after that edit) is calling the Studio endpoint with real ids — verified in
  `logs/open-webui.log`. **Its remaining failure is NOT an endpoint fault:** requests come back
  `HTTP 400 (upstream_error) code=unsupported_parameter` — "Client-supplied tools or tool-call
  history require a GGUF chat template with tool-call support; the current model/template does not
  advertise tools." Open WebUI always sends `tools`; the GGUF templates in use do not advertise tool
  support (the identical error appeared against Ollama with `cydonia-24b`). The fix is on the OWUI
  side — set Function Calling to **Disabled** (or choose a model that advertises tools) in Admin →
  Models — not in the endpoint config. **FIXED 2026-11-06:** its model table held one stale Ollama-era
  row, `cydonia-24b:q8_0` — one of the three tool-incapable ids — so every chat hit the 400.
  `ui.default_models` is now `["qwen3.8-27b-reasoning-medium-q6"]` and the stale row is deactivated
  (`is_active=0`, reversible); OWUI restarted and `/health` → 200. **DB was edited directly, on a
  stopped instance, after a backup to `data/webui.db.bak-20261106`** — a live edit can be overwritten
  by OWUI's in-memory config. Caveat for reasoning models: keep `max_tokens` ≥ 600 (ideally 1200) or
  the allowance goes to thinking and the UI renders an empty/failed message rather than an error.
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

### Unreachable ≠ offline — it is the CUE to re-verify (rule, 2026-11-01)

A service that stops answering is **not** evidence that it is down. A migrated port or host
leaves exactly the same signature as a dead box (`curl` exit 7 / HTTP `000`). So:

1. Probe the service's own surface — `/health`, `/docs`, `/openapi.json`, `/v1/models` — and
   re-read this file's §2 (Rigs/Services) **before** concluding anything.
2. Assume a migration first: Ollama `:11434` → Unsloth Studio `:8888` is the worked example.
3. Then fix the *consumer* (stale pointer, hardcoded endpoint, cached skill copy), not the
   conclusion. Declaring "the box is offline" and stopping is the failure mode this rule exists
   to prevent.

**Do NOT weaken Hermes' default prompt-caching to compensate.** Caching is correct behavior; a
running session holding a stale copy is refreshed by re-reading this file (or by a fresh
session), never by mutating context mid-conversation.

### Local LM Studio loads are killed by TTL — and the error hides it (verified 2026-11-05)

LM Studio's own server log says it outright: `Unloading model qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s
due to TTL expiration.` A 32B was loaded and TTL-unloaded in the same window, so the two models churn
against each other on the 4090. While nothing is resident, an image request returns
`400 {'error': 'terminated'}` (older builds: `400 "Model is unloaded"`) — rejected before it reaches the
model, so the model log shows nothing and it reads like a dead server or a bad image.

- `GET /v1/models` lists models whether loaded or not. **`lms ps` is the authority** and prints the
  instance `TTL` (e.g. `2h / 2h`).
- Pin a working session: `lms load <id> --ttl 7200` (a resident instance keeps its original TTL, so a
  reload/`--force` is needed to change it). Verify with `lms ps` and one image call.
- Helper: `tools/vlm_ready.py --check` / `--force --ttl 7200`. Run it before any VLM batch.
- Hermes `vision_analyze` sends **no system prompt** and prepends "Fully describe and explain everything
  about this image…", which is why it names films/actors. For counts, verdicts or JSON, call
  `/v1/chat/completions` directly with a strict system prompt (`tools/vlm_cast_check.py` is the pattern).
