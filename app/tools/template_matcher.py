from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _score(extents: dict[str, float], target: dict[str, float]) -> float:
    return abs(extents.get("width", 0) - target.get("width", 0)) + abs(extents.get("height", 0) - target.get("height", 0))


def match_pattern(new_site: dict[str, Any], repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or Path(__file__).resolve().parents[2]
    cases_dir = repo_root / "data/extracted_cases"
    pattern_file = repo_root / "data/patterns/patterns.json"

    if not pattern_file.exists():
        raise FileNotFoundError("Pattern cache missing. Run pattern_miner first.")

    candidates = []
    target_extents = new_site.get("extents") or {}
    target_type = new_site.get("site_type")

    for cf in sorted(cases_dir.glob("*.json")):
        case = json.loads(cf.read_text())
        if target_type and case.get("site_type") and case["site_type"] != target_type:
            continue
        ex = case.get("extents") or {}
        candidates.append((case, _score(ex, target_extents)))

    if not candidates:
        raise RuntimeError("No reference case matches the new site constraints")

    best, best_score = min(candidates, key=lambda x: x[1])
    return {"matched_case": best, "score": best_score}


def main() -> None:
    parser = argparse.ArgumentParser(description="Match best reference pattern to new site")
    parser.add_argument("site_json", help="Path to new site extraction json")
    parser.add_argument("--repo-root", default=None)
    args = parser.parse_args()
    site = json.loads(Path(args.site_json).read_text())
    print(json.dumps(match_pattern(site, Path(args.repo_root) if args.repo_root else None), indent=2))


if __name__ == "__main__":
    main()
