from dataclasses import (
    dataclass
)


@dataclass
class ScreenshotComparisonResult:

    success: bool

    confidence: float