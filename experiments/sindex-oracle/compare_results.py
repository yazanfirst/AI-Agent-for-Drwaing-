#!/usr/bin/env python3
import sys
from pathlib import Path

def parse(path):
    phases = {}
    for line in Path(path).read_text(errors="replace").splitlines():
        if not line.startswith("ORACLE_RESULT"):
            continue
        vals = {}
        for item in line.split(",")[1:]:
            k, v = item.split("=", 1)
            vals[k] = int(v)
        phases[vals["phase"]] = vals
    if 1 not in phases:
        raise SystemExit(f"No phase=1 ORACLE_RESULT found in {path}")
    return phases

if len(sys.argv) != 4:
    raise SystemExit("usage: compare_results.py normal.txt oracle_pause.txt no_bg.txt")

normal = parse(sys.argv[1])[1]
oracle = parse(sys.argv[2])[1]
nobg = parse(sys.argv[3])[1]

def pct_improve(old, new):
    return 100.0 * (old - new) / old if old else float("nan")

def pct_change(old, new):
    return 100.0 * (new - old) / old if old else float("nan")

p99_gain = pct_improve(normal["p99_ns"], oracle["p99_ns"])
ops_change = pct_change(normal["ops"], oracle["ops"])
nobg_gain = pct_improve(normal["p99_ns"], nobg["p99_ns"])

print("\n=== PHASE-1 COMPARISON ===")
print(f"normal p99: {normal['p99_ns']} ns")
print(f"oracle p99: {oracle['p99_ns']} ns")
print(f"no-bg  p99: {nobg['p99_ns']} ns")
print(f"oracle p99 improvement vs normal: {p99_gain:.2f}%")
print(f"oracle phase ops change vs normal: {ops_change:.2f}%")
print(f"no-bg p99 improvement vs normal: {nobg_gain:.2f}%")
print(f"samples normal/oracle/no-bg: {normal['samples']}/{oracle['samples']}/{nobg['samples']}")

go = p99_gain >= 20.0 and ops_change >= -5.0
print("\nEXPLORATORY_GATE=" + ("GO" if go else "KILL_OR_REDESIGN"))
if go:
    print("Signal is large enough to justify a stricter repeated experiment.")
else:
    print("The predeclared exploratory signal threshold was not met.")
