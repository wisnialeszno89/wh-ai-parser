from dataclasses import (
    dataclass
)


@dataclass
class QueryModel:

    width: int

    height: int

    pattern: str

    profile: str = ""

    glass: str = ""