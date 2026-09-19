from __future__ import annotations

from app.schemas import LayoutPlan


def render_lod(plan: LayoutPlan, lod: int) -> LayoutPlan:
    if lod not in (100, 200, 300):
        raise ValueError("LOD must be one of 100/200/300")

    rendered = plan.model_copy(deep=True)
    rendered.lod = lod

    if lod == 100:
        rendered.equipment = []
        rendered.seating = []
        rendered.doors = []
    elif lod == 200:
        rendered.equipment = rendered.equipment[: min(10, len(rendered.equipment))]
        rendered.seating = []
        rendered.doors = []
    return rendered
