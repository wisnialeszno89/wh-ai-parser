from dataclasses import (
    dataclass
)


@dataclass
class CustomerPreference:

    customer_name: str

    profile_preference: str

    color_preference: str

    addon_preference: str

    confidence: float