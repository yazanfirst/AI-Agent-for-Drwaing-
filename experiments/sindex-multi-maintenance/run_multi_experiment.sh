#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p build multi_results

CXX=${CXX:-g++}
BIN=build/micro_original_UNIFORM_DIST_multi

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

echo "Runner CPUs: $(nproc)"

COMMON=(
  --fg=1
  --bg=1
  --runtime=20
  --read=0.80
  --insert=0.20
  --update=0
  --remove=0
  --scan=0
  --initial-size=100000
  --table-size=600000
  --target-size=300000
)

run_group() {
  local n="$1"
  local mode="$2"
  local rep="$3"
  local dir="multi_results/n${n}_${mode}_r${rep}"
  mkdir -p "$dir"
  local lockfile="/tmp/sindex-global-bg-${GITHUB_RUN_ID:-local}.lock"
  rm -f "$lockfile"

  # Give every process the same future start time.
  local start_ms
  start_ms=$(( $(date +%s%3N) + 5000 ))

  local pids=()
  for i in $(seq 1 "$n"); do
    if [[ "$mode" == "serial" ]]; then
      SINDEX_BG_LOCK_PATH="$lockfile" SINDEX_START_EPOCH_MS="$start_ms" \
        "$BIN" "${COMMON[@]}" > "$dir/index_${i}.txt" 2>&1 &
    else
      SINDEX_START_EPOCH_MS="$start_ms" \
        "$BIN" "${COMMON[@]}" > "$dir/index_${i}.txt" 2>&1 &
    fi
    pids+=($!)
  done

  local failed=0
  for pid in "${pids[@]}"; do
    if ! wait "$pid"; then
      failed=1
    fi
  done
  if [[ "$failed" -ne 0 ]]; then
    echo "At least one index process failed for n=$n mode=$mode rep=$rep" >&2
    for f in "$dir"/*.txt; do
      echo "--- $f" >&2
      tail -80 "$f" >&2 || true
    done
    exit 4
  fi
}

# Two repetitions. Reverse the mode order on the second repetition to reduce
# systematic bias from thermal / runner state.
for n in 2 4; do
  run_group "$n" local 1
  run_group "$n" serial 1
  run_group "$n" serial 2
  run_group "$n" local 2
done

python3 "$SCRIPT_DIR/compare_multi.py" multi_results
