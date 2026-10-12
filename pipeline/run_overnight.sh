#!/usr/bin/env bash
# Overnight full-film pass: chop all 1308 shots, then keyframes + audio
# stems for the whole feature.
#
# Resumable: chop.py skips clips that already exist and keyframes.py skips
# stills/stems that already exist, so re-running continues rather than
# restarting. The full master audio WAV is already present and is skipped.
set -u

cd "$(dirname "$0")"
PY=".venv/Scripts/python.exe"
LOG="overnight_$(date +%Y%m%d_%H%M%S).log"

echo "=== overnight full-film pass started $(date) ===" | tee -a "$LOG"

# Whole feature. Runtime is 81:38, so a 90-minute window from offset 0
# covers every shot. --no-proxy keeps disk down; proxies are review-only
# and can be generated per-window later.
echo "--- chopping full film (1308 shots, CRF 14 re-encode) ---" | tee -a "$LOG"
"$PY" chop.py --minutes 90 --offset 0 --tag full --no-proxy 2>&1 | tee -a "$LOG"
CHOP_RC=${PIPESTATUS[0]}
echo "chop exit=$CHOP_RC" | tee -a "$LOG"

echo "--- keyframes (first/median/last) + stems ---" | tee -a "$LOG"
"$PY" keyframes.py --minutes 90 --offset 0 --tag full --no-audio-full 2>&1 | tee -a "$LOG"
KF_RC=${PIPESTATUS[0]}
echo "keyframes exit=$KF_RC" | tee -a "$LOG"

echo "=== finished $(date) chop=$CHOP_RC keyframes=$KF_RC ===" | tee -a "$LOG"
if [ "$CHOP_RC" != "0" ] || [ "$KF_RC" != "0" ]; then exit 1; fi
exit 0
