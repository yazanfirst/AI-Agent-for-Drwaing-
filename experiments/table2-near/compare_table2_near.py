#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "table2_near_results")

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

paper={5:3.2,10:4.1,15:4.6}
print("=== TABLE 2 NEAR-PAPER-SCALE SCREEN ===")
print("delete_pct,tput_5s,tput_300s,degradation_pct,paper_pct,abs_gap_percentage_points")
degs=[]
for d in (5,10,15):
    t5,l5=parse(root/f"delete_{d}_interval_5.txt")
    t300,l300=parse(root/f"delete_{d}_interval_300.txt")
    deg=100.0*(t5-t300)/t5
    degs.append(deg)
    print(f"{d},{t5:.0f},{t300:.0f},{deg:.3f},{paper[d]:.1f},{abs(deg-paper[d]):.3f}")

print("\nPAPER_REPORTED: 3.2%, 4.1%, 4.6% degradation at 5%,10%,15% deletion.")
print("MEASURED:", ", ".join(f"{x:.3f}%" for x in degs))
print("same_direction_all_ratios="+str(all(x>0 for x in degs)).lower())
print("within_5_percentage_points_all="+str(all(abs(degs[i]-paper[d])<=5.0 for i,d in enumerate((5,10,15)))).lower())
print("within_10_percentage_points_all="+str(all(abs(degs[i]-paper[d])<=10.0 for i,d in enumerate((5,10,15)))).lower())
