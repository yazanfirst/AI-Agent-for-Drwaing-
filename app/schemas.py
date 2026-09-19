from __future__ import annotations

from typing import Any, Literal, get_type_hints

try:
    from pydantic import BaseModel, Field, model_validator  # type: ignore
except ImportError:  # pragma: no cover
    import copy
    import json

    def Field(default=None, default_factory=None, **_: Any):
        if default_factory is not None:
            return default_factory()
        return default

    def model_validator(*_: Any, **__: Any):
        def decorator(func):
            return func

        return decorator

    class BaseModel:
        def __init__(self, **kwargs: Any):
            hints = get_type_hints(self.__class__)
            for key in hints:
                if key in kwargs:
                    setattr(self, key, kwargs[key])
                elif hasattr(self.__class__, key):
                    setattr(self, key, copy.deepcopy(getattr(self.__class__, key)))
                else:
                    setattr(self, key, None)

        def model_dump(self) -> dict[str, Any]:
            def conv(v: Any):
                if isinstance(v, BaseModel):
                    return v.model_dump()
                if isinstance(v, list):
                    return [conv(x) for x in v]
                if isinstance(v, dict):
                    return {k: conv(val) for k, val in v.items()}
                return v

            return {k: conv(getattr(self, k)) for k in get_type_hints(self.__class__)}

        def model_dump_json(self, indent: int | None = None) -> str:
            return json.dumps(self.model_dump(), indent=indent)

        def model_copy(self, deep: bool = False):
            return copy.deepcopy(self) if deep else copy.copy(self)


class SiteBoundary(BaseModel):
    points: list[tuple[float, float]] = Field(default_factory=list)
    source: str | None = None

    @model_validator(mode="after")
    def _validate_points(self) -> "SiteBoundary":
        if len(self.points) < 3:
            raise ValueError("SiteBoundary requires at least 3 points")
        return self


class Zone(BaseModel):
    zone_id: str
    name: str
    polygon: list[tuple[float, float]] = Field(default_factory=list)
    confidence: float = 1.0


class EquipmentPlacement(BaseModel):
    canonical_name: str
    cad_block_name: str
    x: float
    y: float
    rotation: float = 0.0
    xscale: float = 1.0
    yscale: float = 1.0
    zone_id: str | None = None
    source_case: str | None = None
    unresolved_reason: str | None = None


class SeatingPlacement(BaseModel):
    seating_type: str
    cad_block_name: str
    x: float
    y: float
    rotation: float = 0.0
    count: int = 1
    zone_id: str | None = None


class Door(BaseModel):
    x: float
    y: float
    width: float | None = None
    rotation: float = 0.0
    cad_block_name: str | None = None


class ValidationIssue(BaseModel):
    code: str
    severity: Literal["error", "warning", "info"] = "error"
    message: str = ""
    entity_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValidationReport(BaseModel):
    is_valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)


class LayoutPlan(BaseModel):
    project_id: str
    lod: Literal[100, 200, 300]
    site_boundary: SiteBoundary
    zones: list[Zone] = Field(default_factory=list)
    equipment: list[EquipmentPlacement] = Field(default_factory=list)
    seating: list[SeatingPlacement] = Field(default_factory=list)
    doors: list[Door] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectInput(BaseModel):
    project_id: str
    site_dxf_path: str
    requested_lod: Literal[100, 200, 300]
    site_type: str | None = None
    output_dir: str = "outputs"
    force_refresh: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
