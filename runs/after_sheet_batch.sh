#!/usr/bin/env bash
# After the 13-character photoreal sheet batch lands: resolve it on the rig, pull the sheets, then
# render the S03 two-hander on them (take 6 = corrected (S#) notation + per-shot presence + phantom
# TEEGRA dropped + photoreal sheets) and rebuild the review page.
#
# Waits on the LEDGER, not on a pid: `kill -0 <pid>` does not work for Windows pids from git-bash, so a
# pid-based waiter exits instantly (measured 2026-11-05). The chain writes 13 rows for take 10 when it
# finishes; that count is the honest signal. (It writes them all at the end because this run started
# before I fixed the chain to append per character.)
set -u
cd /e/FNI || exit 1
PY=.venv/Scripts/python.exe
WANT_ROWS=13
MAX_MIN=150
echo "[after-batch] waiting for $WANT_ROWS take-10 rows in the sheet ledger (cap ${MAX_MIN}m)"

for i in $(seq 1 $MAX_MIN); do
  N=$($PY -c "
import json,pathlib
rows=[json.loads(l) for l in pathlib.Path('manifests/photoreal_sheet_chain.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
print(sum(1 for r in rows if str(r.get('take'))=='10' and r.get('action') in ('error-stage2','queued-sheet','wrote-sheet')))
" 2>/dev/null || echo 0)
  if [ "${N:-0}" -ge "$WANT_ROWS" ]; then echo "[after-batch] ledger has $N rows — batch finished"; break; fi
  if [ $((i % 10)) -eq 0 ]; then echo "[after-batch] ${i}m elapsed, ledger rows so far: ${N:-0}"; fi
  sleep 60
done

echo "[after-batch] === step 1: resolve the batch on the 5090 and pull the sheets ==="
$PY tools/verify_photoreal_chain.py 2>&1 | tail -22

echo "[after-batch] === step 2: which photoreal sheets are now on disk? ==="
$PY -c "
import json,pathlib
rows=[json.loads(l) for l in pathlib.Path('manifests/photoreal_sheet_chain.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
ok=[r for r in rows if str(r.get('take'))=='10' and r.get('action')=='wrote-sheet']
print(' pulled:', len(ok), [r['char'] for r in ok])
need={'JULIANA','NEKRON'}
have={r['char'] for r in ok}
print(' S03 needs', need, '-> ready' if need<=have else '-> MISSING '+str(need-have))
"

echo "[after-batch] === step 3: queue take 6 (all fixes + photoreal sheets) for S03-c01/c02 ==="
for c in S03-c01 S03-c02; do
  $PY runs/build_technicolor_audio_only.py --chunk $c --take 6 --shot-presence \
      --subjects JULIANA,NEKRON --queue 2>&1 | tail -2
  # keep the verbatim prompt beside the arms, for the review page and the record
  cp -f "runs/T0016_s05_technicolor-audio-only-ref2va/prompts/$c.txt" \
        "runs/T0017_s03_technicolor-audio-only/prompt_take6_photoreal_sheets_$c.txt" 2>/dev/null
done

echo "[after-batch] === step 4: collect take 6 from the 5090 ==="
FNI_ARM_TAKES=6 $PY runs/collect_s03_arms.py --timeout 30 --interval 30 2>&1 | tail -6

echo "[after-batch] === step 5: rebuild the review page data ==="
$PY tools/build_testruns_data.py 2>&1 | tail -3
echo "[after-batch] DONE"
