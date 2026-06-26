from dataclasses import dataclass

from app.wh.domain.analysis.missing_information import (
    MissingInformation
)


@dataclass(slots=True)
class RequestAnalysis:

    request_complete: bool

    missing: MissingInformation