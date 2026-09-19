from pathlib import Path

import pytest

from app.tools.site_reader import read_site_dxf


def test_site_reader_requires_ezdxf(tmp_path: Path):
    dummy = tmp_path / "a.dxf"
    dummy.write_text("0\nEOF\n")
    with pytest.raises(RuntimeError):
        read_site_dxf(dummy)
