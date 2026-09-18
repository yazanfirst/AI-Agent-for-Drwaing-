#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p build throttle_results

CXX=${CXX:-g++}
BIN=build/micro_original_UNIFORM_DIST_throttle

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
  --bg=1
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

for duty in 1.00 0.75 0.50 0.25; do
  tag=$(echo "$duty" | tr '.' '_')
  echo "=== BG DUTY $duty ==="
  "$BIN" "${COMMON[@]}" --bg-duty="$duty" \
    | tee "throttle_results/duty_${tag}.txt"
done

python3 "$SCRIPT_DIR/compare_throttle.py" throttle_results
