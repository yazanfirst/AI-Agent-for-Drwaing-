#!/usr/bin/env python3
from pathlib import Path
import argparse
import re

ap = argparse.ArgumentParser()
ap.add_argument("repo")
ap.add_argument("--expect-fixed", action="store_true")
args = ap.parse_args()
root = Path(args.repo)

def read(p): return (root/p).read_text(errors="replace")

bench = read("bench.cpp")
lazy = read("scripts/lazy_delete.py")
node = read("scripts/node_size.py")
cmake = read("CMakeLists.txt")
readme = read("README.md")

findings = []

findings.append((
    "BG_ARG_IGNORED",
    "table = new sindex_t(exist_keys, vals, fg_n, 1);" in bench,
    "bench.cpp parses --bg but prepare_sindex hard-codes the SIndex background worker count to 1."
))

m = re.search(r"case 'z':(?P<body>.*?)default:", bench, re.S)
z_bug = bool(m and "ideal_training_interval" in m.group("body") and "break;" not in m.group("body"))
findings.append((
    "IDEAL_TRAINING_OPTION_ABORTS",
    z_bug,
    "The --ideal-training-time switch case falls through to default: abort() because it has no break."
))

lazy_cmd_area = lazy[lazy.find("# Run Microbenchmark"):lazy.find("# Parse")]
lazy_bug = (
    "IDEAL_TRAINING_TIME_LIST" in lazy and
    "for training_time in IDEAL_TRAINING_TIME_LIST" in lazy and
    "--ideal-training-time" not in lazy_cmd_area
)
findings.append((
    "LAZY_DELETE_INTERVAL_NOT_PASSED",
    lazy_bug,
    "lazy_delete.py loops over 5/30/100/300s but does not pass training_time to the executable."
))

twitter_area = node[node.find("# Run Twitter Cache Trace"):node.find("# Parse")]
node_twitter_bug = (
    "for node_accuracy in NODE_ACCURACY_THRESHOLD_LIST" in twitter_area and
    "--sindex-group-err-bound" not in twitter_area and
    "--sindex-root-err-bound" not in twitter_area
)
findings.append((
    "TWITTER_NODE_SIZE_SWEEP_NOT_PASSED",
    node_twitter_bug,
    "node_size.py labels Twitter runs with different node_accuracy values but passes no error-bound setting."
))

cmake_disabled = (
    "# foreach(Test IN LISTS TestList)" in cmake and
    "# foreach(Dist IN LISTS DistList)" in cmake
)
findings.append((
    "SINDEX_CMAKE_TARGETS_DISABLED",
    cmake_disabled,
    "CMake blocks that define original/sia-sw/ideal benchmark targets are commented out."
))

readme_target_bug = "PERFORMANCE_sia-sw_bench_{DISTRIBUTION}" in readme
findings.append((
    "README_MICRO_TARGET_MISMATCH",
    readme_target_bug,
    "README documents PERFORMANCE_sia-sw_bench_{DISTRIBUTION}, while CMake defines micro_{Index}_{Dist}."
))

bad = [x for x in findings if x[1]]
print("SIA ARTIFACT AUDIT")
print("="*72)
for name, present, explanation in findings:
    state = "DEFECT_PRESENT" if present else "not detected"
    print(f"{name}: {state}")
    print(f"  {explanation}")
print("="*72)
print(f"defects_detected={len(bad)}")

if args.expect_fixed and bad:
    raise SystemExit("Expected fixed tree, but defects remain: " + ", ".join(x[0] for x in bad))
