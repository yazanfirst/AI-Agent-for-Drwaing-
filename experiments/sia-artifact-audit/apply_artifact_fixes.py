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

replace_once(
    "scripts/lazy_delete.py",
    """                        --table-size={DATASET_SIZE}         \
                        > ../results/lazy_delete_{delete_ratio}_{training_time}_{i}.txt")
""",
    """                        --table-size={DATASET_SIZE}         \
                        --ideal-training-time={training_time}     \
                        > ../results/lazy_delete_{delete_ratio}_{training_time}_{i}.txt")
"""
)

replace_once(
    "scripts/node_size.py",
    """                                    --cluster-number={cluster}  \
                                    > ../results/node_size_{index}_{cluster}_{node_accuracy}_{i}.txt')
""",
    """                                    --cluster-number={cluster}                  \
                                    --sindex-group-err-bound={node_accuracy}    \
                                    --sindex-root-err-bound={node_accuracy}     \
                                    > ../results/node_size_{index}_{cluster}_{node_accuracy}_{i}.txt')
"""
)

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
