#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "throttle_results")

def parse(path):
    phases = {}
    for line in path.read_text(errors="replace").splitlines():
        if not line.startswith("ORACLE_RESULT"):
            continue
        vals = {}
        for item in line.split(",")[1:]:
            k, v = item.split("=", 1)
            vals[k] = int(v)
        phases[vals["phase"]] = vals
    if 1 not in phases:
        raise SystemExit(f"Missing phase=1 in {path}")
    return phases[1]

files = {
    1.00: root / "duty_1_00.txt",
    0.75: root / "duty_0_75.txt",
    0.50: root / "duty_0_50.txt",
    0.25: root / "duty_0_25.txt",
}
rows = {d: parse(p) for d,p in files.items()}
base = rows[1.00]

def improve(old, new):
    return 100.0 * (old-new) / old

def change(old, new):
    return 100.0 * (new-old) / old

print("\n=== THROTTLE PHASE-1 COMPARISON ===")
print("duty,p99_ns,p999_ns,ops,p99_gain_pct,p999_change_pct,ops_change_pct")
survivors = []
for duty in [1.00,0.75,0.50,0.25]:
    r = rows[duty]
    p99_gain = improve(base["p99_ns"], r["p99_ns"])
    p999_change = change(base["p999_ns"], r["p999_ns"])
    ops_change = change(base["ops"], r["ops"])
    print(f"{duty:.2f},{r['p99_ns']},{r['p999_ns']},{r['ops']},"
          f"{p99_gain:.2f},{p999_change:.2f},{ops_change:.2f}")
    if duty < 1.0 and p99_gain >= 10.0 and p999_change <= 10.0 and ops_change >= -5.0:
        survivors.append(duty)

print("\nPREDECLARED_GATE:",
      "GO " + ",".join(f"{d:.2f}" for d in survivors)
      if survivors else "KILL_OR_REDESIGN")
if survivors:
    print("At least one throttle level cleared the exploratory gate.")
else:
    print("No throttle level cleared: p99 gain >=10%, p99.9 worsening <=10%, ops loss <=5%.")
