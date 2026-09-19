from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.tools.site_reader import read_site_dxf


def _resolve_references_dir(base: Path) -> Path:
    for c in (base / "data/references", base / "data/ references"):
        if c.exists():
            return c
    raise FileNotFoundError("No references directory found")


def _best_site_boundary(polylines: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [p for p in polylines if p.get("closed") and len(p.get("points", [])) >= 3]
    if not candidates:
        return None

    def area(poly: dict[str, Any]) -> float:
        pts = poly["points"]
        a = 0.0
        for i in range(len(pts)):
            x1, y1, _ = pts[i]
            x2, y2, _ = pts[(i + 1) % len(pts)]
            a += x1 * y2 - x2 * y1
        return abs(a) * 0.5

    chosen = max(candidates, key=area)
    return {
        "source": "largest_closed_polyline",
        "points": chosen["points"],
        "area": area(chosen),
        "layer": chosen.get("layer"),
    }


def extract_reference_case(dxf_path: Path) -> dict[str, Any]:
    raw = read_site_dxf(dxf_path)
    block_usage = Counter(i["block_name"] for i in raw["inserts"])
    return {
        "source_file": str(dxf_path),
        "extents": raw.get("extents"),
        "site_boundary": _best_site_boundary(raw.get("polylines", [])),
        "block_usage": dict(block_usage),
        "insert_positions": raw.get("inserts", []),
        "text_labels": raw.get("text", []),
        "uncertainties": [
            "site_boundary_unresolved" if _best_site_boundary(raw.get("polylines", [])) is None else None
        ],
    }


def extract_all_reference_cases(repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or Path(__file__).resolve().parents[2]
    refs_dir = _resolve_references_dir(repo_root)
    out_dir = repo_root / "data/extracted_cases"
    out_dir.mkdir(parents=True, exist_ok=True)

    dxf_files = sorted(p for p in refs_dir.glob("*.dxf") if p.is_file())
    cases = []
    for dxf in dxf_files:
        case = extract_reference_case(dxf)
        case["uncertainties"] = [u for u in case["uncertainties"] if u]
        out_file = out_dir / f"{dxf.stem}.json"
        out_file.write_text(json.dumps(case, indent=2))
        cases.append({"source": str(dxf), "output": str(out_file)})

    return {"count": len(cases), "cases": cases, "output_dir": str(out_dir)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract structured reference cases from DXFs")
    parser.add_argument("--repo-root", default=None)
    args = parser.parse_args()
    print(json.dumps(extract_all_reference_cases(Path(args.repo_root) if args.repo_root else None), indent=2))


if __name__ == "__main__":
    main()
