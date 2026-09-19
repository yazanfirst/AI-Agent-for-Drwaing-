#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p thread_sensitivity_results
BIN=./build/micro_ideal_UNIFORM_DIST

export MKL_THREADING_LAYER=SEQUENTIAL
export LD_LIBRARY_PATH=/opt/intel/oneapi/mkl/latest/lib/intel64:${LD_LIBRARY_PATH:-}

RUNTIME=30
INITIAL=10000000
TARGET=100000000
TABLE=100000000

for fg in 4 16; do
  for del in 5 10 15; do
    case "$del" in
      5)  read=0.95; remove=0.05 ;;
      10) read=0.90; remove=0.10 ;;
      15) read=0.85; remove=0.15 ;;
    esac
    for interval in 5 300; do
      out="thread_sensitivity_results/fg_${fg}_delete_${del}_interval_${interval}.txt"
      echo "=== fg=$fg delete=$del% interval=${interval}s ==="
      "$BIN"         --fg="$fg" --bg=1 --runtime="$RUNTIME"         --read="$read" --remove="$remove"         --insert=0 --update=0 --scan=0         --initial-size="$INITIAL" --target-size="$TARGET" --table-size="$TABLE"         --ideal-training-time="$interval"         | tee "$out"
    done
  done
done

python3 "$SCRIPT_DIR/compare_thread_sensitivity.py" thread_sensitivity_results
