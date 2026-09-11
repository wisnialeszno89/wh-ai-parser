from dataclasses import dataclass

from app.context.context_source import ContextSource


@dataclass(frozen=True)
class DecisionOverride:
    """
    Explicit decision that can override another value.

    In practice this is primarily used for salesman instructions,
    for example when the requested product must be priced using
    another available WH configuration.
    """

    field: str
    value: str
    reason: str
    source: ContextSource = ContextSource.SALESMAN
