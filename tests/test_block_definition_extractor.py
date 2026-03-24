from pathlib import Path

from app.tools.block_definition_extractor import _resolve_references_dir


def test_resolve_references_dir_with_spaced_name(tmp_path: Path):
    (tmp_path / "data/ references").mkdir(parents=True)
    found = _resolve_references_dir(tmp_path)
    assert found.name == " references"
