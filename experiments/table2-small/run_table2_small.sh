#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p table2_small_results

BIN=./build/micro_ideal_UNIFORM_DIST
if [[ ! -x "$BIN" ]]; then
  echo "Missing $BIN" >&2
  exit 2
fi

export MKL_THREADING_LAYER=SEQUENTIAL
export LD_LIBRARY_PATH=/opt/intel/oneapi/mkl/latest/lib/intel64:${LD_LIBRARY_PATH:-}

FG=4
RUNTIME=30
INITIAL=500000
TARGET=500000
TABLE=500000

for del in 5 10 15; do
  case "$del" in
    5)  read=0.95; remove=0.05 ;;
    10) read=0.90; remove=0.10 ;;
    15) read=0.85; remove=0.15 ;;
  esac

  for interval in 5 30 100 300; do
    out="table2_small_results/delete_${del}_interval_${interval}.txt"
    echo "=== delete=${del}% interval=${interval}s ==="
    "$BIN"       --fg="$FG" --bg=1 --runtime="$RUNTIME"       --read="$read" --remove="$remove"       --insert=0 --update=0 --scan=0       --initial-size="$INITIAL" --target-size="$TARGET" --table-size="$TABLE"       --ideal-training-time="$interval"       | tee "$out"
  done
done

python3 "$SCRIPT_DIR/compare_table2_small.py" table2_small_results
