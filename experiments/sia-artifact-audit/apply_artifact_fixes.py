#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()

def replace_once(rel, old, new):
    p=ROOT/rel
    s=p.read_text()
    n=s.count(old)
    if n != 1:
        raise SystemExit(f"{rel}: expected one occurrence, found {n}")
    p.write_text(s.replace(old,new,1))
    print("[fixed]", rel)

replace_once(
    "bench.cpp",
    "table = new sindex_t(exist_keys, vals, fg_n, 1);",
    "table = new sindex_t(exist_keys, vals, fg_n, bg_n);"
)

replace_once(
    "bench.cpp",
    """      case 'z':
        ideal_training_interval = strtoul(optarg, NULL, 10);
      default:
""",
    """      case 'z':
        ideal_training_interval = strtoul(optarg, NULL, 10);
        break;
      default:
"""
)

p=ROOT/"scripts/lazy_delete.py"
s=p.read_text()
needle="                        --table-size={DATASET_SIZE}         " + "\\" + "\n"
if s.count(needle) != 1:
    raise SystemExit(f"scripts/lazy_delete.py: expected one table-size command line, found {s.count(needle)}")
insert=needle + "                        --ideal-training-time={training_time}     " + "\\" + "\n"
p.write_text(s.replace(needle, insert, 1))
print("[fixed] scripts/lazy_delete.py")

p=ROOT/"scripts/node_size.py"
s=p.read_text()
needle="                                    --cluster-number={cluster}  " + "\\" + "\n"
if s.count(needle) != 1:
    raise SystemExit(f"scripts/node_size.py: expected one Twitter cluster command line, found {s.count(needle)}")
insert=(needle
        + "                                    --sindex-group-err-bound={node_accuracy}    " + "\\" + "\n"
        + "                                    --sindex-root-err-bound={node_accuracy}     " + "\\" + "\n")
p.write_text(s.replace(needle, insert, 1))
print("[fixed] scripts/node_size.py")

p=ROOT/"CMakeLists.txt"
s=p.read_text()

def uncomment_region(s, start_marker, end_marker):
    a=s.index(start_marker)
    b=s.index(end_marker, a)
    block=s[a:b]
    out=[]
    for line in block.splitlines(True):
        if line.startswith("# "):
            line=line[2:]
        elif line.startswith("#"):
            line=line[1:]
        out.append(line)
    return s[:a]+"".join(out)+s[b:]

s=uncomment_region(
    s,
    "# foreach(Test IN LISTS TestList)",
    "list(APPEND DistList"
)
s=uncomment_region(
    s,
    "# foreach(Dist IN LISTS DistList)",
    "# # Build cuckoo-trie"
)
p.write_text(s)
print("[fixed] CMakeLists.txt benchmark target blocks")

replace_once(
    "README.md",
    "./build/PERFORMANCE_sia-sw_bench_{DISTRIBUTION}",
    "./build/micro_sia-sw_{DISTRIBUTION}"
)

print("All guarded artifact fixes applied.")
