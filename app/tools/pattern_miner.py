from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def mine_patterns(repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or Path(__file__).resolve().parents[2]
    cases_dir = repo_root / "data/extracted_cases"
    pattern_dir = repo_root / "data/patterns"
    pattern_dir.mkdir(parents=True, exist_ok=True)

    case_files = sorted(cases_dir.glob("*.json"))
    if not case_files:
        return {"case_count": 0, "message": "No extracted cases available"}

    block_counts = Counter()
    cooccurrence = Counter()
    adjacency = Counter()
    extents = []

    for cf in case_files:
        case = json.loads(cf.read_text())
        usage = case.get("block_usage", {})
        block_counts.update(usage)

        present = sorted(usage)
        for pair in itertools.combinations(present, 2):
            cooccurrence[pair] += 1

        inserts = case.get("insert_positions", [])
        for a, b in itertools.combinations(inserts, 2):
            ap = tuple(a.get("insert", [0, 0])[:2])
            bp = tuple(b.get("insert", [0, 0])[:2])
            if _distance(ap, bp) <= 2000.0:
                key = tuple(sorted((a.get("block_name", "?"), b.get("block_name", "?"))))
                adjacency[key] += 1

        ex = case.get("extents") or {}
        if ex:
            extents.append({"width": ex.get("width", 0), "height": ex.get("height", 0)})

    patterns = {
        "case_count": len(case_files),
        "common_block_clusters": [{"blocks": list(k), "count": v} for k, v in cooccurrence.most_common(50)],
        "equipment_cooccurrence": [{"pair": list(k), "count": v} for k, v in cooccurrence.most_common(100)],
        "adjacency_patterns": [{"pair": list(k), "count": v} for k, v in adjacency.most_common(100)],
        "typical_extents": {
            "count": len(extents),
            "avg_width": sum(e["width"] for e in extents) / max(len(extents), 1),
            "avg_height": sum(e["height"] for e in extents) / max(len(extents), 1),
        },
        "block_popularity": dict(block_counts.most_common()),
    }

    (pattern_dir / "patterns.json").write_text(json.dumps(patterns, indent=2))

    by_type: dict[str, Any] = defaultdict(list)
    for cf in case_files:
        c = json.loads(cf.read_text())
        st = c.get("site_type") or "unknown"
        by_type[st].append(c)
    (pattern_dir / "pattern_index.json").write_text(json.dumps({"site_type_index": list(by_type.keys())}, indent=2))
    return patterns


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine reusable patterns from extracted cases")
    parser.add_argument("--repo-root", default=None)
    args = parser.parse_args()
    print(json.dumps(mine_patterns(Path(args.repo_root) if args.repo_root else None), indent=2))


if __name__ == "__main__":
    main()
