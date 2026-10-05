#!/bin/bash
# Drain the remainder of the FNI full run: wait for the 5090 queue to empty,
# then collect and stitch. Does NOT touch the ledger while the render loop owns
# it — collect only appends on top of /history lookups, and stitch reads files.
set -u
cd /e/FNI
export PYTHONUNBUFFERED=1

echo "=== drain start $(date) ==="
for i in $(seq 1 1440); do
  run_pend=$(curl -s -m 10 http://192.168.12.177:8188/queue | python -c "import json,sys;d=json.load(sys.stdin);print(len(d['queue_running'])+len(d['queue_pending']))" 2>/dev/null || echo 999)
  echo "iter $i $(date '+%H:%M:%S'): queue=$run_pend"
  if [ "$run_pend" = "0" ]; then
    echo "=== queue drained $(date) ==="
    break
  fi
  sleep 120
done

echo "=== collect $(date) ==="
python fullrun.py collect | tail -1

echo "=== stitch $(date) ==="
python fullrun.py stitch

echo "=== status $(date) ==="
python fullrun.py status
echo "=== ALL DONE $(date) ==="