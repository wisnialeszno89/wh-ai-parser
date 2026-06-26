from dataclasses import (
    dataclass
)


@dataclass
class SecurityPackage:

    rc2: bool = False

    contacts: bool = False