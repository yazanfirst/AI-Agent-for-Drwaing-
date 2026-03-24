from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _require_ezdxf():
    try:
        import ezdxf  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("ezdxf is required. Install with `pip install ezdxf`.") from exc


def _resolve_references_dir(base: Path) -> Path:
    candidates = [base / "data/references", base / "data/ references"]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError("No references directory found in data/references or data/ references")


def extract_block_definitions_from_dxf(dxf_path: Path) -> list[dict[str, Any]]:
    import ezdxf  # type: ignore

    doc = ezdxf.readfile(str(dxf_path))
    found: list[dict[str, Any]] = []
    for block in doc.blocks:
        entities = []
        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")

        for e in block:
            etype = e.dxftype()
            entity_info: dict[str, Any] = {"type": etype}

            if e.dxf.hasattr("layer"):
                entity_info["layer"] = e.dxf.layer

            points: list[tuple[float, float]] = []
            if etype == "LINE":
                s, t = e.dxf.start, e.dxf.end
                points = [(float(s.x), float(s.y)), (float(t.x), float(t.y))]
            elif etype == "CIRCLE":
                c = e.dxf.center
                r = float(e.dxf.radius)
                points = [(float(c.x - r), float(c.y - r)), (float(c.x + r), float(c.y + r))]
            elif etype in {"LWPOLYLINE", "POLYLINE"}:
                if etype == "LWPOLYLINE":
                    points = [(float(p[0]), float(p[1])) for p in e.get_points("xy")]
                else:
                    points = [(float(v.dxf.location.x), float(v.dxf.location.y)) for v in e.vertices]
            elif e.dxf.hasattr("insert"):
                p = e.dxf.insert
                points = [(float(p.x), float(p.y))]

            if points:
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                min_x, min_y = min(min_x, min(xs)), min(min_y, min(ys))
                max_x, max_y = max(max_x, max(xs)), max(max_y, max(ys))
                entity_info["points"] = points

            entities.append(entity_info)

        bbox = None
        if min_x != float("inf"):
            bbox = {"min": [min_x, min_y], "max": [max_x, max_y], "width": max_x - min_x, "height": max_y - min_y}

        found.append(
            {
                "source_file": str(dxf_path),
                "block_name": block.name,
                "base_point": [float(block.base_point[0]), float(block.base_point[1]), float(block.base_point[2])],
                "entity_count": len(entities),
                "entities": entities,
                "approx_bbox": bbox,
            }
        )
    return found


def extract_all_blocks(repo_root: Path | None = None) -> dict[str, Any]:
    _require_ezdxf()
    repo_root = repo_root or Path(__file__).resolve().parents[2]
    refs_dir = _resolve_references_dir(repo_root)
    dxf_files = sorted(p for p in refs_dir.glob("*.dxf") if p.is_file())

    blocks: list[dict[str, Any]] = []
    for path in dxf_files:
        blocks.extend(extract_block_definitions_from_dxf(path))

    out = {
        "reference_dir": str(refs_dir),
        "files_processed": [str(x) for x in dxf_files],
        "block_count": len(blocks),
        "blocks": blocks,
    }
    output_path = repo_root / "data/equipment/block_definitions_extracted.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out, indent=2))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract block definitions from reference DXFs")
    parser.add_argument("--repo-root", default=None)
    args = parser.parse_args()
    result = extract_all_blocks(Path(args.repo_root) if args.repo_root else None)
    print(json.dumps({"block_count": result["block_count"], "output": "data/equipment/block_definitions_extracted.json"}, indent=2))


if __name__ == "__main__":
    main()
