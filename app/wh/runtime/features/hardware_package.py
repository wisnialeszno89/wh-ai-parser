from dataclasses import (
    dataclass
)


@dataclass
class HardwarePackage:

    hidden_hinges: bool = False

    v_perfect: bool = False