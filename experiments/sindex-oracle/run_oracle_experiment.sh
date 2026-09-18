#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(pwd)"

if [[ ! -f "$REPO_ROOT/bench.cpp" || ! -f "$REPO_ROOT/original/sindex.h" ]]; then
  echo "Run this script from the SIA repository root." >&2
  exit 2
fi

mkdir -p build oracle_results

CXX=${CXX:-g++}
BIN=build/micro_original_UNIFORM_DIST_oracle

if [[ -f /opt/intel/oneapi/mkl/latest/include/mkl.h ]]; then
  MKLROOT=/opt/intel/oneapi/mkl/latest
elif [[ -f /opt/intel/mkl/include/mkl.h ]]; then
  MKLROOT=/opt/intel/mkl
else
  echo "Intel oneMKL headers not found." >&2
  exit 3
fi

MKL_LIB="$MKLROOT/lib"
if [[ -d "$MKLROOT/lib/intel64" ]]; then
  MKL_LIB="$MKLROOT/lib/intel64"
fi

echo "Using MKLROOT=$MKLROOT"

"$CXX" \
  -std=c++14 -O3 -DNDEBUGGING -DMAX_KEY_SIZE=32 -DUNIFORM_DIST \
  -march=native -mtune=native -faligned-new \
  -I. -Ioriginal -I"$MKLROOT/include" \
  bench.cpp \
  -L"$MKL_LIB" \
  -Wl,-rpath,"$MKL_LIB" \
  -Wl,--start-group -lmkl_intel_lp64 -lmkl_sequential -lmkl_core -Wl,--end-group \
  -lpthread -lm -ldl \
  -o "$BIN"

COMMON=(
  --fg=4
  --runtime=30
  --read=0.80
  --insert=0.20
  --update=0
  --remove=0
  --scan=0
  --initial-size=100000
  --table-size=1000000
  --target-size=500000
)

echo "=== 1/3 NORMAL: background maintenance enabled continuously ==="
"$BIN" "${COMMON[@]}" --bg=1 | tee oracle_results/normal.txt

echo "=== 2/3 ORACLE: defer new background rounds from t=10s to t=20s ==="
"$BIN" "${COMMON[@]}" --bg=1 \
  --oracle-pause-start=10 \
  --oracle-pause-end=20 \
  | tee oracle_results/oracle_pause.txt

echo "=== 3/3 NO-BG CONTROL: maintenance disabled ==="
"$BIN" "${COMMON[@]}" --bg=0 | tee oracle_results/no_bg.txt

echo
python3 "$SCRIPT_DIR/compare_results.py" \
  oracle_results/normal.txt \
  oracle_results/oracle_pause.txt \
  oracle_results/no_bg.txt
