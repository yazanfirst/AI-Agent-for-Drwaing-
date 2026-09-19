import json
from pathlib import Path

from app.tools.pattern_miner import mine_patterns


def test_pattern_miner_counts_cases(tmp_path: Path):
    extracted = tmp_path / "data/extracted_cases"
    extracted.mkdir(parents=True)
    (tmp_path / "data/patterns").mkdir(parents=True)

    case = {
        "block_usage": {"A": 1, "B": 2},
        "insert_positions": [
            {"block_name": "A", "insert": [0, 0, 0]},
            {"block_name": "B", "insert": [1, 1, 0]},
        ],
        "extents": {"width": 10, "height": 20},
    }
    (extracted / "c1.json").write_text(json.dumps(case))
    patterns = mine_patterns(tmp_path)
    assert patterns["case_count"] == 1
    assert patterns["typical_extents"]["avg_width"] == 10
