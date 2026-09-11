from dataclasses import dataclass

from app.context.context_source import ContextSource


@dataclass(frozen=True)
class DecisionValue:
    """
    Resolved final value together with information about
    where the value came from.
    """

    field: str
    value: str | None
    source: ContextSource
    reason: str
