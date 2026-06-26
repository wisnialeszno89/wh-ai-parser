from dataclasses import (
    dataclass,
    field
)


@dataclass
class ConfigurationReport:

    problems: list = field(

        default_factory=list

    )

    suggestions: list = field(

        default_factory=list

    )

    optimized_offer = None