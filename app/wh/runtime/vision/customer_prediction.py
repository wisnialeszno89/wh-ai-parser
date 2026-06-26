from dataclasses import (
    dataclass
)


@dataclass
class CustomerPrediction:

    customer_name: str

    profile: str

    color: str

    addon: str

    confidence: float