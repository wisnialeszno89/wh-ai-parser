from pydantic import BaseModel
from typing import List, Optional


class VisionSegment(BaseModel):
    kind: str
    opening: Optional[str] = None


class VisionConstruction(BaseModel):
    category: Optional[str] = None

    width_mm: Optional[int] = None
    height_mm: Optional[int] = None

    segments: List[VisionSegment] = []

    confidence: Optional[float] = None