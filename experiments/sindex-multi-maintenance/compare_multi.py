#!/usr/bin/env python3
from pathlib import Path
import statistics
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "multi_results")

def phase1(path):
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("ORACLE_RESULT") and ",phase=1," in line:
            vals = {}
            for item in line.split(",")[1:]:
                k, v = item.split("=", 1)
                vals[k] = int(v)
            return vals
    raise RuntimeError(f"No phase=1 result in {path}")

def summarize(n, mode, rep):
    d = root / f"n{n}_{mode}_r{rep}"
    rows = [phase1(p) for p in sorted(d.glob("index_*.txt"))]
    if len(rows) != n:
        raise RuntimeError(f"Expected {n} result files in {d}, got {len(rows)}")
    return {
        "ops": sum(r["ops"] for r in rows),
        "worst_p99": max(r["p99_ns"] for r in rows),
        "worst_p999": max(r["p999_ns"] for r in rows),
        "median_p99": int(statistics.median(r["p99_ns"] for r in rows)),
        "samples": sum(r["samples"] for r in rows),
    }

def pct_improve(old, new):
    return 100.0 * (old - new) / old

def pct_change(old, new):
    return 100.0 * (new - old) / old

print("=== MULTI-INDEX BACKGROUND-MAINTENANCE COORDINATION ===")
print("n,rep,mode,aggregate_ops,worst_p99_ns,worst_p999_ns,median_p99_ns,samples")

all_data = {}
for n in (2,4):
    for rep in (1,2):
        for mode in ("local","serial"):
            s = summarize(n,mode,rep)
            all_data[(n,rep,mode)] = s
            print(f"{n},{rep},{mode},{s['ops']},{s['worst_p99']},"
                  f"{s['worst_p999']},{s['median_p99']},{s['samples']}")

print("\n=== EFFECT OF SERIALIZING MAINTENANCE ===")
survivors = []
for n in (2,4):
    gains=[]
    op_changes=[]
    p999_gains=[]
    positive_reps=0
    for rep in (1,2):
        local=all_data[(n,rep,"local")]
        serial=all_data[(n,rep,"serial")]
        g=pct_improve(local["worst_p99"],serial["worst_p99"])
        g999=pct_improve(local["worst_p999"],serial["worst_p999"])
        oc=pct_change(local["ops"],serial["ops"])
        gains.append(g); p999_gains.append(g999); op_changes.append(oc)
        if g > 0:
            positive_reps += 1
        print(f"n={n} rep={rep}: p99_gain={g:.2f}% "
              f"p999_gain={g999:.2f}% ops_change={oc:.2f}%")
    mg=statistics.mean(gains)
    mg999=statistics.mean(p999_gains)
    moc=statistics.mean(op_changes)
    print(f"n={n} mean: p99_gain={mg:.2f}% p999_gain={mg999:.2f}% "
          f"ops_change={moc:.2f}%")
    # Predeclared screening gate:
    # - >=10% mean worst-index p99 improvement
    # - no more than 5% aggregate ops loss
    # - p99 improves in both repetitions (not one lucky run)
    if mg >= 10.0 and moc >= -5.0 and positive_reps == 2:
        survivors.append(n)

print("\nPREDECLARED_GATE:",
      "GO n=" + ",".join(map(str,survivors))
      if survivors else "KILL_OR_REDESIGN")
