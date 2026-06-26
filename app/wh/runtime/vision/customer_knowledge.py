from dataclasses import (
    dataclass
)


@dataclass
class CustomerKnowledge:

    customer_name: str

    top_profiles: list[str]

    top_colors: list[str]

    top_addons: list[str]