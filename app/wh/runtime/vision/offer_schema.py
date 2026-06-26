from dataclasses import (
    dataclass
)


@dataclass
class OfferSchema:

    customer_name: str

    profile: str

    color: str

    addon: str