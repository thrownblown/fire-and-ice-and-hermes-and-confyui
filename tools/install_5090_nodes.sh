#!/usr/bin/env bash
# Run ON the 5090 (the render box). Installs the H3 chaining/timeline node packs
# and prints the restart + verification steps.
#
#   bash install_5090_nodes.sh
#
# Defaults assume ComfyUI at $HOME/comfyvenv/ComfyUI (that is where this project's
# box keeps it, per its own temp paths). Override if yours differs:
#   COMFY_DIR=/path/to/ComfyUI bash install_5090_nodes.sh
#
# Why these two: chanon/comfyui-obvpm-timeline gives extend / prepend / BRIDGE /
# cut / loop + a timeline node, built on NikoDemon80/ComfyUI-H3-Motion-Context,
# which provides the motion-context (latent) primitives. Bridging is the candidate
# replacement for FNI's first/last-frame chain anchoring.
set -euo pipefail

COMFY_DIR="${COMFY_DIR:-$HOME/comfyvenv/ComfyUI}"
CN="$COMFY_DIR/custom_nodes"
mkdir -p "$CN"

for repo in \
  https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context \
  https://github.com/chanon/comfyui-obvpm-timeline ; do
  name="$(basename "$repo")"
  if [ -d "$CN/$name/.git" ]; then
    echo "== updating $name"
    git -C "$CN/$name" pull --ff-only
  else
    echo "== cloning $name"
    git clone --depth 1 "$repo" "$CN/$name"
  fi
done

echo "== installed:"
ls -d "$CN/ComfyUI-H3-Motion-Context" "$CN/comfyui-obvpm-timeline" 2>/dev/null

UP="$COMFY_DIR/models/latent_upscale_models"
mkdir -p "$UP"
[ -f "$UP/minimax_h3_latent_upscaler_3d_conv_v1_fp16.safetensors" ] || \
  echo "== note: latent upscaling (not chaining) additionally wants
   minimax_h3_latent_upscaler_3d_conv_v1_fp16.safetensors in $UP
   from huggingface.co/LBH-123-AI/Minimax_h3_latent_Upscaler"

cat <<'EOF'

Now restart ComfyUI (kill the process tree, start it again), then verify from anywhere on the tailnet:

  curl -s http://100.104.7.72:8188/object_info \
    | grep -oE 'MiniMaxH3MotionContext[A-Za-z]*|H3Timeline|H3JointRender|H3Assemble' | sort -u

Expect MiniMaxH3MotionContext, MiniMaxH3MotionContextTrim, MiniMaxH3MotionContextChain,
MiniMaxH3MotionContextSaveLatent, MiniMaxH3MotionContextLoadLatent, H3Timeline, H3JointRender,
H3Assemble. Tell Hermes when it is up and it will build the anchoring-vs-bridging A/B.
EOF
