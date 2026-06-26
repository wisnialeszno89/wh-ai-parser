from dataclasses import (
    dataclass
)


@dataclass
class ConfigurationProblem:

    code: str

    message: str