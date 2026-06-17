from dataclasses import (
    dataclass
)


@dataclass
class TopologySignature:

    rows: int

    columns: int

    balanced: bool

    single_row: bool

    single_column: bool