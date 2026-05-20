from pydantic import BaseModel
from typing import List


class SegmentResult(BaseModel):

    segments: List[str]