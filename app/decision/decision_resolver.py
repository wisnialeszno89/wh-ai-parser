from app.context.context_source import ContextSource
from app.decision.decision_override import DecisionOverride
from app.decision.decision_value import DecisionValue


class DecisionResolver:
    """
    Resolve a final decision from a base value and explicit overrides.

    Current priority:

    SALESMAN override
        >
    base value

    The class is intentionally small because additional priority
    levels can later be introduced without changing the public API.
    """

    def resolve(
        self,
        *,
        field: str,
        value: str | None,
        source: ContextSource,
        reason: str,
        overrides: list[DecisionOverride] | None = None,
    ) -> DecisionValue:

        overrides = overrides or []

        matching_overrides = [
            override
            for override in overrides
            if override.field == field
        ]

        if matching_overrides:
            override = matching_overrides[-1]

            return DecisionValue(
                field=field,
                value=override.value,
                source=override.source,
                reason=override.reason,
            )

        return DecisionValue(
            field=field,
            value=value,
            source=source,
            reason=reason,
        )
