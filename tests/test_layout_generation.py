import json
from pathlib import Path

from app.tools.layout_adapter import adapt_layout
from app.tools.lod_renderer import render_lod
from app.tools.validator import validate_layout


def test_layout_generation_marks_unresolved(tmp_path: Path):
    equipment = tmp_path / "data/equipment"
    equipment.mkdir(parents=True)
    (equipment / "block_catalog_from_drawings.json").write_text(json.dumps({"canonical_mappings": {}}))

    matched = {
        "score": 1.0,
        "matched_case": {
            "source_file": "ref.dxf",
            "site_boundary": {"points": [[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]], "source": "test"},
            "insert_positions": [{"block_name": "FRYER", "insert": [5, 5, 0]}],
        },
    }
    plan = adapt_layout(matched, "p1", 300, tmp_path)
    rendered = render_lod(plan, 300)
    report = validate_layout(rendered)
    assert report.is_valid is False
    assert any(i.code == "MISSING_CAD_BLOCK" for i in report.issues)
