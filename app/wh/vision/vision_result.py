from dataclasses import dataclass

from app.wh.vision.match_result import (
    MatchResult
)


@dataclass
class VisionResult:

    group: str

    template_name: str

    match_result: MatchResult