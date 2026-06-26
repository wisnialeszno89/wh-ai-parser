from dataclasses import (
    dataclass
)


@dataclass
class OfferVerificationResult:

    success: bool

    confidence: float

    message: str = ""