from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.schemas import EquipmentPlacement, LayoutPlan, SiteBoundary, Zone


def _load_block_catalog(repo_root: Path) -> dict[str, str]:
    cat_file = repo_root / "data/equipment/block_catalog_from_drawings.json"
    data = json.loads(cat_file.read_text())
    mappings = data.get("canonical_mappings", {})
    out = {}
    for canonical, entry in mappings.items():
        if isinstance(entry, dict):
            name = entry.get("block_name") or entry.get("preferred_block")
        else:
            name = str(entry)
        if name:
            out[canonical] = name
    return out


def adapt_layout(matched: dict[str, Any], project_id: str, lod: int, repo_root: Path | None = None) -> LayoutPlan:
    repo_root = repo_root or Path(__file__).resolve().parents[2]
    block_map = _load_block_catalog(repo_root)
    case = matched["matched_case"]
    boundary_raw = case.get("site_boundary")

    if not boundary_raw:
        raise ValueError("Cannot adapt layout without site boundary")

    zones = [
        Zone(zone_id="kitchen", name="kitchen", polygon=[], confidence=0.0),
        Zone(zone_id="dining", name="dining", polygon=[], confidence=0.0),
        Zone(zone_id="support", name="support", polygon=[], confidence=0.0),
    ]

    placements: list[EquipmentPlacement] = []
    for ins in case.get("insert_positions", []):
        canonical = ins.get("block_name")
        block_name = block_map.get(canonical)
        unresolved_reason = None
        if not block_name:
            block_name = "UNRESOLVED"
            unresolved_reason = "cad_block_not_found_in_catalog"

        placements.append(
            EquipmentPlacement(
                canonical_name=canonical,
                cad_block_name=block_name,
                x=float(ins["insert"][0]),
                y=float(ins["insert"][1]),
                rotation=float(ins.get("rotation", 0.0)),
                xscale=float(ins.get("xscale", 1.0)),
                yscale=float(ins.get("yscale", 1.0)),
                zone_id=None,
                source_case=case.get("source_file"),
                unresolved_reason=unresolved_reason,
            )
        )

    plan = LayoutPlan(
        project_id=project_id,
        lod=lod,
        site_boundary=SiteBoundary(points=[(p[0], p[1]) for p in boundary_raw["points"]], source=boundary_raw.get("source")),
        zones=zones,
        equipment=placements,
        metadata={"match_score": matched.get("score")},
    )
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Adapt matched template into a concrete layout")
    parser.add_argument("matched_json", help="Path to matcher output json")
    parser.add_argument("--project-id", default="new-project")
    parser.add_argument("--lod", type=int, default=300)
    parser.add_argument("--repo-root", default=None)
    args = parser.parse_args()

    matched = json.loads(Path(args.matched_json).read_text())
    plan = adapt_layout(matched, args.project_id, args.lod, Path(args.repo_root) if args.repo_root else None)
    print(plan.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
