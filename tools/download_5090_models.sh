#!/usr/bin/env bash
# Run ON the 5090 (the render box). Downloads the H3 models the community rates
# that the box does NOT already have, into the right ComfyUI folders.
#
#   bash download_5090_models.sh                    # tier 1 (recommended, ~23 GB)
#   bash download_5090_models.sh all                # tier 1 + 2 (~27 GB)
#   bash download_5090_models.sh loras              # tier-1 LoRAs only (~1.3 GB)
#   bash download_5090_models.sh lora-retro-fantasy # Civitai style LoRA only (~569 MB)
#   bash download_5090_models.sh lora-technicolor   # Technicolor/80s-fantasy H3 LoRAs (~600 MB)
#
# Defaults assume ComfyUI at $HOME/comfyvenv/ComfyUI (where this project's box
# keeps it). Override:  COMFY_DIR=/path/to/ComfyUI bash download_5090_models.sh
#
# Why these (r/StableDiffusion 1x1g4mu + 1x4auud + veterans thread):
#   Singularity ref2va  = community's #1 ref2va base; the base in Dainamo's refmod WF.
#   Larry V4 600 EMA    = the one turbo LoRA users say does NOT wreck the audio (8 steps).
#   Kijai DMAD rank-reduced = fixes the shiny/plastic skin most turbo LoRAs cause (~5 steps).
#   fal realism-people  = cheap skin-realism LoRA, part of the community refmod stack.
# Already on the box (do NOT re-download): official fl2va/ref2va pruned int8_convrot,
# the w4a8 pair, Eros Max turbo-hybrid, Ref-Delta-Fused r1024, fastvideo VSA 4step,
# qwen3vl_32b nvfp4_awq + heretic, the H3 VAEs + taeh3, LightX2V turbo 4/8-step (ref2v +
# fl2v), silver-dareties, raven-4nfe, ACC-8step (FL2VA + Ref2VA), the motion boosters,
# ref_lora_rank_256, the 3D latent upscaler.
set -euo pipefail

COMFY_DIR="${COMFY_DIR:-$HOME/comfyvenv/ComfyUI}"
DM="$COMFY_DIR/models/diffusion_models/h3"
LR="$COMFY_DIR/models/loras/h3"
MP="$COMFY_DIR/models/model_patches"
LU="$COMFY_DIR/models/latent_upscale_models"
mkdir -p "$DM" "$LR" "$MP" "$LU"

MODE="${1:-tier1}"
H=https://huggingface.co

get() {  # get <url> <dest-dir>
  local url="$1" dest="$2" f
  f="$(basename "$url")"
  if [ -f "$dest/$f" ]; then echo "== have $f"; return 0; fi
  echo "== fetching $f"
  curl -4 -L --fail --retry 3 -C - -o "$dest/$f.part" "$url"
  mv "$dest/$f.part" "$dest/$f"
}

get_named() {  # get_named <url> <dest-dir> <filename> [sha256]
  local url="$1" dest="$2" f="$3" want="$4" got
  if [ -f "$dest/$f" ]; then echo "== have $f"; else
    echo "== fetching $f"
    # Civitai returns 401 without a browser User-Agent.
    curl -4 -L --fail --retry 3 -A "Mozilla/5.0" -C - -o "$dest/$f.part" "$url"
    mv "$dest/$f.part" "$dest/$f"
  fi
  if [ -n "$want" ]; then
    got="$(sha256sum "$dest/$f" | cut -d' ' -f1 | tr 'a-f' 'A-F')"
    if [ "$got" = "$want" ]; then echo "   sha256 OK"; else
      echo "   !! sha256 MISMATCH for $f"
      echo "      want $want"
      echo "      got  $got"
    fi
  fi
}

# Civitai LoRAs (no auth needed for these). --lora-retro-fantasy
civitai_retro_fantasy() {
  echo "## Civitai LoRA: MiniMax H3 — Forgotten World's - Retro Fantasy (style)"
  # "Minimax H3 Forgotten World's Retro Fantasy" by Granddyser, v3388934, 2026-10-07.
  # Optional trigger: retr0Fantasy. 16:9 most reliable; prefers a START FRAME over pure t2v.
  # Landing it in loras/h3/ so it shows under the h3/ group in LoraLoader.
  get_named "https://civitai.com/api/download/models/3388934?fileId=3278075" \
    "$LR" "retro-fantasy.safetensors" \
    "27EF791C0DF87A0AA877D6BD3CB6F37C6053FDF3E3F28093D4386811B3702E9B"
}

# Civitai LoRAs for the Technicolor 80s sword-and-sandals direction (docs/technicolor-lora-stack.md).
# Caveat: Civitai 401s without a browser User-Agent — get_named() must send one.
civitai_technicolor() {
  echo "## Civitai LoRAs: Technicolor / 80s fantasy style (H3)"
  mkdir -p "$LR/80s-technicolor"
  # ArsMachina's "Movie Still Styles" line — the only era look that exists for BOTH Krea 2
  # (stills) and MiniMax H3 (video). Images-only style LoRAs: lock every frame, no motion training.
  # Trigger both: "ArsMovieStill, ...". On an H3 turbo LoRA raise strength to 1.2–1.7 (turbo
  # diminishes the style), else 1.2. Apply with LoraLoaderModelOnly.
  get_named "https://civitai.com/api/download/models/3339781?fileId=3226392" \
    "$LR" "80s-technicolor/30sTechnicolorMovie_minimaxh3_3339408_epoch_10.safetensors"
  get_named "https://civitai.com/api/download/models/3337011?fileId=3223514" \
    "$LR" "80s-technicolor/80sFantasyMovie_minimaxh3_3333584_epoch_10.safetensors"
  # Alternative broad cinematic grades (optional, untested):
  #   Cinematic Fantasy        2957855 v3350636  https://civitai.com/api/download/models/3350636
  #   CinemaGrade (cinemagradestyle) 2927223 v3312531 https://civitai.com/api/download/models/3312531
}

if [ "$MODE" = "lora-technicolor" ] || [ "$MODE" = "civitai" ]; then
  civitai_technicolor
fi

if [ "$MODE" = "lora-retro-fantasy" ] || [ "$MODE" = "civitai" ]; then
  civitai_retro_fantasy
  echo "## done. Restart ComfyUI, then confirm it is listed:"
  echo "  curl -s http://127.0.0.1:8188/object_info | grep -o 'h3/retro-fantasy[^\"]*' | head -1"
  exit 0
fi

echo "## tier 1 — base model + the three LoRAs"
# Singularity ref2va base (20.97 GB). w4a8 alternative: ..._ref2va_v1.3_Pruned_w4a8.safetensors (11.77 GB)
get "$H/WarmBloodAban/Minimax-h3_Singularity/resolve/main/Minimax-h3_Singularity_ref2va_Pruned_v1.3_int8.safetensors" "$DM"
get "$H/WarmBloodAban/Minimax-h3_Singularity/resolve/main/MiniMax_H3_Singularity_Prompt_Writing_Specification_Enhanced_EN.md" "$DM"

# Larry's V4 600-step turbo LoRA, EMA build (0.78 GB) — audio-safe speedup at 8 steps.
# NOTE: needs the node pack Larryvrh/ComfyUI-MiniMax-H3-Turbo (run install_5090_nodes.sh).
# README guidance: v4-600 EMA is the recommended checkpoint; use 6-8 steps (at 4 steps with
# large/fast motion v4 can smear -> the older v1 ~850 is friendlier there).
get "$H/larryvrh/MiniMax-H3-Turbo-Lora/resolve/main/minimax_h3_turbo_v4_step600_ema.safetensors" "$LR"
# Larry's 4-step EMA (0.78 GB) — faster draft option.
get "$H/larryvrh/MiniMax-H3-Turbo-Lora/resolve/main/minimax_h3_turbo_4step_ema.safetensors" "$LR"

# Kijai rank-reduced DMAD (0.37 GB) — shiny/plastic-skin fix, good from ~5 steps.
get "$H/Kijai/MiniMax-H3-experimental/resolve/main/loras/minimax_h3_DMAD_4step_full_lora_avg_rank_39_bf16.safetensors" "$LR"
# fal realism-people (0.13 GB) — skin realism, used in the refmod stack.
get "$H/fal/MiniMax-H3-Realism-People-LoRA/resolve/main/h3-realism-people-t2v-i2v-r2v.safetensors" "$LR"

# Community-finetuned H3 latent upscaler (0.69 GB) — sharper than stock; from the
# "seamless long videos / no colour shift" workflow (r/comfyui 1wz3s0q).
get "$H/Alissonerdx/Minimax-H3-ComfyUI/resolve/main/latent_upscaler/h3_upscaler_lms_v0.1.safetensors" "$LU"

if [ "$MODE" = "loras" ]; then echo "== loras-only run done"; exit 0; fi

if [ "$MODE" = "all" ]; then
  echo "## tier 2 — alternative turbo LoRAs + Fun ControlNet"
  # Kijai pdmd 2-step (0.38 GB) and 4-step (0.56 GB) — alternative few-step LoRAs.
  get "$H/Kijai/MiniMax-H3-experimental/resolve/main/loras/minimax_h3_pdmd_2step_lora_avg_rank_38_bf16.safetensors" "$LR"
  get "$H/Kijai/MiniMax-H3-experimental/resolve/main/loras/minimax_h3_pdmd_4step_lora_avg_rank_57_bf16.safetensors" "$LR"
  # Kijai ELM longlive 4-step (1.96 GB) — for longer clips.
  get "$H/Kijai/MiniMax-H3-experimental/resolve/main/loras/minimax_h3_ELM_longlive_plug_4step_lora_bf16.safetensors" "$LR"
  # Fun ControlNet union, int8 (2.30 GB) — composition control (not wired into FNI yet).
  get "$H/Kijai/MiniMax-H3-experimental/resolve/main/model_patches/minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors" "$MP"
fi

echo "## done. Verify from anywhere on the tailnet:"
echo "  curl -s http://100.104.7.72:8188/object_info \\"
echo "    | grep -oE 'Singularity_ref2va[A-Za-z0-9_.-]*|turbo_v4_step600[A-Za-z0-9_.-]*|DMAD[A-Za-z0-9_.-]*' | sort -u"
echo "Restart ComfyUI (kill the process tree, start again) so the new files appear in the loaders."
