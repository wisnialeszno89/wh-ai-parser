from pydantic import BaseModel
from typing import Optional

from app.models.enums import SegmentKind
from app.models.enums import OpeningMode


class Segment(BaseModel):

    segment_id: int

    kind: SegmentKind

    opening_mode: OpeningMode

    width_mm: int

    opening_side: Optional[str] = None

    movable_mullion: bool = False