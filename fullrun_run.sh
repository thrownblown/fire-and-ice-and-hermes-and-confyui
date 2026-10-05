#!/bin/bash
# Full-film FNI run. Caption pass on the 4090 (local qwen3-vl-8b via LM Studio),
# render queue on the 5090. Both resumable; re-running skips finished work.
#
#   nohup bash fullrun_run.sh > fullrun/fullrun.log 2>&1 &
#
# The render loop refreshes each chunk's prompt from the caption cache as it goes,
# so renders issued late in the run still pick up captions that landed after the
# initial full prompt pass.
set -u
cd /e/FNI
export PYTHONUNBUFFERED=1

echo "=== caption pass $(date) ==="
python fullrun.py caption --workers 2
echo "=== caption pass done $(date) ==="

echo "=== prompt pass $(date) ==="
python fullrun.py prompt
echo "=== prompt pass done $(date) ==="

# max-pending 6 keeps the 5090 fed without stacking hundreds of untested graphs.
# --refresh rebuilds each prompt from the newest captions before queueing.
echo "=== render pass $(date) ==="
python fullrun.py render --max-pending 6 --poll 60 --gap 3 --refresh
echo "=== render pass done $(date) ==="

# collect, then loop until nothing is left missing (renders can still be in flight)
for i in 1 2 3 4 5 6 7 8 9 10; do
  echo "=== collect pass $i $(date) ==="
  python fullrun.py collect
  sleep 120
done

echo "=== stitch $(date) ==="
python fullrun.py stitch
echo "=== status $(date) ==="
python fullrun.py status
echo "=== ALL DONE $(date) ==="
