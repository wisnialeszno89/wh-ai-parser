from dataclasses import dataclass


@dataclass
class OpenCVMatch:

    x: int

    y: int

    confidence: float