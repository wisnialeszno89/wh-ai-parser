from pydantic import BaseModel
from typing import List, Optional


class SegmentSchema(BaseModel):
    kind: str
    opening: Optional[str] = None


class GeometrySchema(BaseModel):

    category: Optional[str] = None

    width_mm: Optional[int] = None
    height_mm: Optional[int] = None

    segments: List[SegmentSchema]

    confidence: Optional[float] = None