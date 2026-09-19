#!/usr/bin/env python3
from pathlib import Path
import math
import statistics
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "repeat_results")
paper={5:3.2,10:4.1,15:4.6}

def parse(path):
    for line in path.read_text(errors="replace").splitlines():
        if "[micro] Throughput(op/s):" in line:
            return float(line.split()[-1])
    raise RuntimeError(f"missing throughput in {path}")

print("=== REPEATED TABLE 2 SCREEN (10M keys, 16 fg) ===")
print("delete,rep,tput5,tput300,degradation_pct")
summary={}
for d in (5,10,15):
    vals=[]
    for rep in (1,2,3):
        a=parse(root/f"delete_{d}_interval_5_rep_{rep}.txt")
        b=parse(root/f"delete_{d}_interval_300_rep_{rep}.txt")
        deg=100*(a-b)/a
        vals.append(deg)
        print(f"{d},{rep},{a:.0f},{b:.0f},{deg:.3f}")
    mean=statistics.mean(vals)
    sd=statistics.stdev(vals)
    # t critical df=2 for two-sided 95% CI
    half=4.303*sd/math.sqrt(3)
    summary[d]=(mean,sd,half,min(vals),max(vals))
    print(f"delete={d}% mean={mean:.3f}% sd={sd:.3f}pp 95CI=[{mean-half:.3f},{mean+half:.3f}] "
          f"range=[{min(vals):.3f},{max(vals):.3f}] paper={paper[d]:.1f}%")

print("\n=== STABILITY ===")
for d in (5,10,15):
    mean,sd,half,lo,hi=summary[d]
    print(f"delete={d}%: run_range_width={hi-lo:.3f}pp paper_gap={mean-paper[d]:.3f}pp")

print("\nNOTE: n=3 gives a wide CI. This is a screening test of repeatability, not a publication-grade confidence estimate.")
