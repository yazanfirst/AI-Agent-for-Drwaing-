from __future__ import annotations

import json
from pathlib import Path

from app.schemas import LayoutPlan


def export_layout_json(plan: LayoutPlan, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(plan.model_dump_json(indent=2))
    return output_path


def export_layout_dxf(plan: LayoutPlan, output_path: Path) -> Path:
    try:
        import ezdxf  # type: ignore
    except ImportError as exc:
        raise RuntimeError("ezdxf is required for DXF export") from exc

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    boundary = plan.site_boundary.points
    if boundary:
        msp.add_lwpolyline(boundary + [boundary[0]], dxfattribs={"layer": "SITE_BOUNDARY"})

    for eq in plan.equipment:
        if eq.cad_block_name == "UNRESOLVED":
            continue
        try:
            msp.add_blockref(
                eq.cad_block_name,
                (eq.x, eq.y),
                dxfattribs={"rotation": eq.rotation, "xscale": eq.xscale, "yscale": eq.yscale, "layer": "EQUIPMENT"},
            )
        except Exception:
            # Unknown block definition in output template: keep explicit unresolved info in JSON only.
            continue

    for seat in plan.seating:
        if seat.cad_block_name != "UNRESOLVED":
            try:
                msp.add_blockref(seat.cad_block_name, (seat.x, seat.y), dxfattribs={"rotation": seat.rotation, "layer": "SEATING"})
            except Exception:
                continue

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(output_path)
    return output_path


def export_all(plan: LayoutPlan, output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = export_layout_json(plan, output_dir / f"{plan.project_id}_layout_lod{plan.lod}.json")
    dxf_path = export_layout_dxf(plan, output_dir / f"{plan.project_id}_layout_lod{plan.lod}.dxf")
    return {"json": str(json_path), "dxf": str(dxf_path)}
