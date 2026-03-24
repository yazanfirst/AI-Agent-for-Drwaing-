from app.tools.reference_extractor import _best_site_boundary


def test_best_site_boundary_selects_largest_closed_polyline():
    result = _best_site_boundary(
        [
            {"closed": True, "points": [(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)]},
            {"closed": True, "points": [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]},
        ]
    )
    assert result is not None
    assert result["area"] == 4.0
