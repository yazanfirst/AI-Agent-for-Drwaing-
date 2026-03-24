from __future__ import annotations

from app.schemas import LayoutPlan, ValidationIssue, ValidationReport


def _point_in_polygon(x: float, y: float, poly: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        intersects = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi)
        if intersects:
            inside = not inside
        j = i
    return inside


def validate_layout(plan: LayoutPlan) -> ValidationReport:
    issues: list[ValidationIssue] = []
    boundary = plan.site_boundary.points

    for idx, eq in enumerate(plan.equipment):
        if eq.cad_block_name == "UNRESOLVED" or eq.unresolved_reason:
            issues.append(
                ValidationIssue(
                    code="MISSING_CAD_BLOCK",
                    severity="error",
                    message=f"Equipment '{eq.canonical_name}' has unresolved CAD block mapping",
                    entity_id=f"equipment:{idx}",
                )
            )

        if not _point_in_polygon(eq.x, eq.y, boundary):
            issues.append(
                ValidationIssue(
                    code="OUTSIDE_BOUNDARY",
                    severity="error",
                    message=f"Equipment '{eq.canonical_name}' point is outside site boundary",
                    entity_id=f"equipment:{idx}",
                )
            )

    seen_xy: dict[tuple[float, float], int] = {}
    for idx, eq in enumerate(plan.equipment):
        key = (round(eq.x, 3), round(eq.y, 3))
        if key in seen_xy:
            issues.append(
                ValidationIssue(
                    code="POTENTIAL_OVERLAP",
                    severity="warning",
                    message="Multiple equipment placements share the same insertion point",
                    entity_id=f"equipment:{idx}",
                    metadata={"other_index": seen_xy[key]},
                )
            )
        seen_xy[key] = idx

    if not plan.equipment:
        issues.append(
            ValidationIssue(
                code="MISSING_EQUIPMENT",
                severity="error",
                message="Layout has no equipment placements",
            )
        )

    is_valid = not any(i.severity == "error" for i in issues)
    return ValidationReport(is_valid=is_valid, issues=issues)
