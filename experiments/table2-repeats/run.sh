#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p repeat_results
BIN=./build/micro_ideal_UNIFORM_DIST

export MKL_THREADING_LAYER=SEQUENTIAL
export LD_LIBRARY_PATH=/opt/intel/oneapi/mkl/latest/lib/intel64:${LD_LIBRARY_PATH:-}

FG=16
RUNTIME=30
INITIAL=10000000
TARGET=100000000
TABLE=100000000

run_one() {
  local del="$1" interval="$2" rep="$3"
  local read remove
  case "$del" in
    5) read=0.95; remove=0.05 ;;
    10) read=0.90; remove=0.10 ;;
    15) read=0.85; remove=0.15 ;;
  esac
  local out="repeat_results/delete_${del}_interval_${interval}_rep_${rep}.txt"
  echo "=== rep=$rep delete=$del% interval=${interval}s ==="
  "$BIN"     --fg="$FG" --bg=1 --runtime="$RUNTIME"     --read="$read" --remove="$remove"     --insert=0 --update=0 --scan=0     --initial-size="$INITIAL" --target-size="$TARGET" --table-size="$TABLE"     --ideal-training-time="$interval"     | tee "$out"
}

# Three paired repetitions. Reverse interval order in rep 2 to reduce order bias.
for del in 5 10 15; do
  run_one "$del" 5 1
  run_one "$del" 300 1

  run_one "$del" 300 2
  run_one "$del" 5 2

  run_one "$del" 5 3
  run_one "$del" 300 3
done

python3 "$SCRIPT_DIR/analyze_repeats.py" repeat_results
