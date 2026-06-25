from typing import Any, Literal

from pydantic import BaseModel, Field


class H3PreviewRequest(BaseModel):
    polygon: dict[str, Any] = Field(..., description="GeoJSON Polygon or MultiPolygon")
    resolution: int | None = Field(default=None, ge=0, le=15)
    include_cells: bool = False
    max_cells: int | None = Field(
        default=1000,
        ge=1,
        description="Maximum number of H3 cells to return when include_cells is true. Use null for all cells.",
    )


class H3PreviewResponse(BaseModel):
    resolution: int
    cell_count: int
    returned_cell_count: int
    h3_cells_bigint: list[int]
    bbox: list[float]
    geometry_type: Literal["Polygon", "MultiPolygon"]
