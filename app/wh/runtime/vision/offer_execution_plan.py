from dataclasses import (
    dataclass
)


@dataclass
class OfferExecutionPlan:

    customer_name: str

    profile: str

    color: str

    addon: str