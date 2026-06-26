from dataclasses import (
    dataclass
)


@dataclass
class RollbackResult:

    success: bool

    restored_snapshot: object | None = None