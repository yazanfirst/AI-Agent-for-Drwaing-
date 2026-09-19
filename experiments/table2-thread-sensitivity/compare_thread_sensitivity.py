#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "thread_sensitivity_results")
paper={5:3.2,10:4.1,15:4.6}

def parse(path):
    t=None
    for line in path.read_text(errors="replace").splitlines():
        if "[micro] Throughput(op/s):" in line:
            t=float(line.split()[-1])
    if t is None:
        raise RuntimeError(f"missing throughput: {path}")
    return t

print("=== THREAD SENSITIVITY AT 10M KEYS ===")
print("fg,delete_pct,tput_5s,tput_300s,degradation_pct,paper_pct")
results={}
for fg in (4,16):
    for d in (5,10,15):
        t5=parse(root/f"fg_{fg}_delete_{d}_interval_5.txt")
        t300=parse(root/f"fg_{fg}_delete_{d}_interval_300.txt")
        deg=100*(t5-t300)/t5
        results[(fg,d)]=deg
        print(f"{fg},{d},{t5:.0f},{t300:.0f},{deg:.3f},{paper[d]:.1f}")

print("\n=== EFFECT OF OVERSUBSCRIPTION (16 FG ON 4 CPU RUNNER) ===")
for d in (5,10,15):
    a=results[(4,d)]
    b=results[(16,d)]
    print(f"delete={d}%: fg4_penalty={a:.3f}% fg16_penalty={b:.3f}% delta={b-a:.3f}pp")

mae4=sum(abs(results[(4,d)]-paper[d]) for d in (5,10,15))/3
mae16=sum(abs(results[(16,d)]-paper[d]) for d in (5,10,15))/3
print(f"\nmean_abs_gap_to_paper_fg4={mae4:.3f}pp")
print(f"mean_abs_gap_to_paper_fg16={mae16:.3f}pp")
print("closer_to_paper="+("fg4" if mae4 < mae16 else "fg16"))
