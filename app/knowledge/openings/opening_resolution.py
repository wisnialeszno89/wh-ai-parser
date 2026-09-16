from dataclasses import dataclass
from enum import Enum


class OpeningResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    NOT_FOUND = "not_found"


@dataclass(frozen=True)
class OpeningResolution:
    status: OpeningResolutionStatus
    code: str | None = None
    matches: tuple[str, ...] = ()

    @property
    def is_resolved(self) -> bool:
        return (
            self.status
            == OpeningResolutionStatus.RESOLVED
        )

    @property
    def is_ambiguous(self) -> bool:
        return (
            self.status
            == OpeningResolutionStatus.AMBIGUOUS
        )

    @property
    def is_not_found(self) -> bool:
        return (
            self.status
            == OpeningResolutionStatus.NOT_FOUND
        )
