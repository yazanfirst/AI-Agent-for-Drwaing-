from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _require_ezdxf():
    try:
        import ezdxf  # type: ignore
    except ImportError as exc:
        raise RuntimeError("ezdxf is required. Install with `pip install ezdxf`.") from exc
    return ezdxf


def _as_point(value: Any) -> tuple[float, float, float]:
    try:
        return (float(value.x), float(value.y), float(getattr(value, "z", 0.0)))
    except AttributeError:
        if isinstance(value, (list, tuple)):
            v = list(value) + [0.0, 0.0, 0.0]
            return (float(v[0]), float(v[1]), float(v[2]))
        return (0.0, 0.0, 0.0)


def read_site_dxf(dxf_path: str | Path) -> dict[str, Any]:
    ezdxf = _require_ezdxf()

    dxf_path = Path(dxf_path)
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()

    lines: list[dict[str, Any]] = []
    polylines: list[dict[str, Any]] = []
    inserts: list[dict[str, Any]] = []
    texts: list[dict[str, Any]] = []
    layers = sorted(layer.dxf.name for layer in doc.layers)

    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    def update_extents(points: list[tuple[float, float, float]]) -> None:
        nonlocal min_x, min_y, max_x, max_y
        for px, py, _ in points:
            min_x = min(min_x, px)
            min_y = min(min_y, py)
            max_x = max(max_x, px)
            max_y = max(max_y, py)

    for entity in msp:
        etype = entity.dxftype()
        layer = entity.dxf.layer if entity.dxf.hasattr("layer") else None
        if etype == "LINE":
            start = _as_point(entity.dxf.start)
            end = _as_point(entity.dxf.end)
            update_extents([start, end])
            lines.append({"layer": layer, "start": start, "end": end})

        elif etype in {"LWPOLYLINE", "POLYLINE"}:
            if etype == "LWPOLYLINE":
                pts = [
                    (float(p[0]), float(p[1]), 0.0)
                    for p in entity.get_points("xy")
                ]
                is_closed = bool(entity.closed)
            else:
                pts = [_as_point(v.dxf.location) for v in entity.vertices]
                is_closed = bool(entity.is_closed)

            update_extents(pts)
            polylines.append(
                {
                    "layer": layer,
                    "points": pts,
                    "closed": is_closed,
                    "entity_type": etype,
                }
            )

        elif etype == "INSERT":
            ins = _as_point(entity.dxf.insert)
            update_extents([ins])
            inserts.append(
                {
                    "layer": layer,
                    "block_name": entity.dxf.name,
                    "insert": ins,
                    "rotation": float(getattr(entity.dxf, "rotation", 0.0)),
                    "xscale": float(getattr(entity.dxf, "xscale", 1.0)),
                    "yscale": float(getattr(entity.dxf, "yscale", 1.0)),
                }
            )

        elif etype in {"TEXT", "MTEXT"}:
            if etype == "TEXT":
                txt = entity.dxf.text
                p = _as_point(entity.dxf.insert)
            else:
                txt = entity.plain_text()
                p = _as_point(entity.dxf.insert)
            update_extents([p])
            texts.append({"layer": layer, "text": txt, "insert": p, "entity_type": etype})

    if min_x == float("inf"):
        extents = None
    else:
        extents = {"min": [min_x, min_y], "max": [max_x, max_y], "width": max_x - min_x, "height": max_y - min_y}

    return {
        "file": str(dxf_path),
        "units": str(doc.units),
        "layers": layers,
        "lines": lines,
        "polylines": polylines,
        "inserts": inserts,
        "text": texts,
        "extents": extents,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract DXF site geometry and entities")
    parser.add_argument("dxf_path", type=str)
    parser.add_argument("--indent", type=int, default=2)
    args = parser.parse_args()
    data = read_site_dxf(args.dxf_path)
    print(json.dumps(data, indent=args.indent))


if __name__ == "__main__":
    main()
