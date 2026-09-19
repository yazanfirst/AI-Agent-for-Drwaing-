#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "table2_small_results")

def parse(path):
    tput=None
    lat=None
    for line in path.read_text(errors="replace").splitlines():
        if "[micro] Throughput(op/s):" in line:
            tput=float(line.split()[-1])
        elif "[micro] Latency:" in line:
            lat=float(line.split()[-1])
    if tput is None:
        raise RuntimeError(f"No throughput in {path}")
    return tput,lat

rows={}
for d in (5,10,15):
    for iv in (5,30,100,300):
        rows[(d,iv)]=parse(root/f"delete_{d}_interval_{iv}.txt")

print("=== TABLE 2 SMALL REPRODUCTION ===")
print("delete_pct,interval_s,throughput_ops_s,avg_latency_s,degradation_vs_5s_pct")
for d in (5,10,15):
    base=rows[(d,5)][0]
    for iv in (5,30,100,300):
        t,l=rows[(d,iv)]
        deg=100.0*(base-t)/base
        print(f"{d},{iv},{t:.0f},{l:.9g},{deg:.3f}")

print("\n=== 300s vs 5s ===")
degs=[]
for d in (5,10,15):
    b=rows[(d,5)][0]
    t=rows[(d,300)][0]
    deg=100.0*(b-t)/b
    degs.append(deg)
    print(f"delete={d}%: degradation={deg:.3f}%")

same_direction=all(x>0 for x in degs)
increasing=degs[0] < degs[1] < degs[2]
meaningful=all(x>=1.0 for x in degs)

print("\nPAPER_REPORTED_300S_DEGRADATION: 5%=3.2%, 10%=4.1%, 15%=4.6%")
print(f"same_direction_all_ratios={str(same_direction).lower()}")
print(f"penalty_increases_with_delete_ratio={str(increasing).lower()}")
print(f"all_penalties_at_least_1pct={str(meaningful).lower()}")

if same_direction and increasing and meaningful:
    print("SCREENING_GATE=SIGNAL_SURVIVES")
else:
    print("SCREENING_GATE=INCONCLUSIVE_OR_NO_SIGNAL")
