from dataclasses import dataclass
from enum import Enum


class DecisionKind(str, Enum):
    FACT = "fact"
    DEFAULT = "default"
    RULE = "rule"
    COMPATIBILITY = "compatibility"
    SALESMAN_DECISION = "salesman_decision"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DecisionTrace:
    field: str
    value: str | None
    kind: DecisionKind
    source: str
    reason: str
