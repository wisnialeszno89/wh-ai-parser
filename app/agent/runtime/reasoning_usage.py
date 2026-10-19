from dataclasses import dataclass, field


OPENAI_PRICING_USD_PER_1M: dict[str, tuple[float, float, float]] = {
    # Current standard API pricing for gpt-4.1-mini:
    # input $0.40 / cached input $0.10 / output $1.60 per 1M tokens.
    "gpt-4.1-mini": (0.40, 0.10, 1.60),
}


def estimate_openai_cost_usd(
    *,
    model: str,
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
) -> float | None:
    normalized_model = model.strip().casefold()

    pricing = OPENAI_PRICING_USD_PER_1M.get(
        normalized_model
    )
    if pricing is None:
        return None

    input_rate, cached_input_rate, output_rate = pricing
    cached_tokens = min(
        max(cached_input_tokens, 0),
        max(input_tokens, 0),
    )
    uncached_tokens = max(input_tokens, 0) - cached_tokens

    return (
        (
            uncached_tokens * input_rate
            + cached_tokens * cached_input_rate
            + max(output_tokens, 0) * output_rate
        )
        / 1_000_000
    )


@dataclass(frozen=True)
class ReasoningUsage:
    """Provider-reported usage for one semantic reasoning call."""

    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cached_input_tokens: int = 0
    reasoning_tokens: int = 0
    estimated_cost_usd: float | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "cached_input_tokens",
            "reasoning_tokens",
        ):
            value = getattr(self, field_name)
            if value < 0:
                raise ValueError(
                    f"{field_name} must be non-negative."
                )

        if self.cached_input_tokens > self.input_tokens:
            raise ValueError(
                "cached_input_tokens cannot exceed input_tokens."
            )

        if self.estimated_cost_usd is not None and self.estimated_cost_usd < 0:
            raise ValueError(
                "estimated_cost_usd must be non-negative."
            )

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, object],
    ) -> "ReasoningUsage":
        provider = payload.get("provider")
        model = payload.get("model")

        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("reasoning_usage_missing_provider")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("reasoning_usage_missing_model")

        values: dict[str, int] = {}
        for key in (
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "cached_input_tokens",
            "reasoning_tokens",
        ):
            raw = payload.get(key, 0)
            try:
                value = int(raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"reasoning_usage_invalid_{key}"
                ) from exc
            values[key] = value

        estimated_cost = estimate_openai_cost_usd(
            model=model,
            input_tokens=values["input_tokens"],
            cached_input_tokens=values["cached_input_tokens"],
            output_tokens=values["output_tokens"],
        ) if provider.strip().casefold() == "openai" else None

        return cls(
            provider=provider.strip(),
            model=model.strip(),
            input_tokens=values["input_tokens"],
            output_tokens=values["output_tokens"],
            total_tokens=values["total_tokens"],
            cached_input_tokens=values["cached_input_tokens"],
            reasoning_tokens=values["reasoning_tokens"],
            estimated_cost_usd=estimated_cost,
        )

    @property
    def uncached_input_tokens(self) -> int:
        return self.input_tokens - self.cached_input_tokens

    def to_payload(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
        }


@dataclass(frozen=True)
class ReasoningCostSummary:
    """Aggregate reasoning usage for one autonomous run."""

    calls: int = 0
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: int = 0
    estimated_cost_usd: float | None = 0.0
    models: tuple[str, ...] = ()

    @property
    def uncached_input_tokens(self) -> int:
        return self.input_tokens - self.cached_input_tokens

    def to_payload(self) -> dict[str, object]:
        return {
            "calls": self.calls,
            "input_tokens": self.input_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "uncached_input_tokens": self.uncached_input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "models": self.models,
        }


@dataclass
class ReasoningCostTracker:
    """Collect provider-reported reasoning usage during a run."""

    usages: list[ReasoningUsage] = field(default_factory=list)

    def record(self, usage: ReasoningUsage) -> None:
        self.usages.append(usage)

    def summary(self) -> ReasoningCostSummary:
        if not self.usages:
            return ReasoningCostSummary()

        costs = [
            usage.estimated_cost_usd
            for usage in self.usages
        ]

        return ReasoningCostSummary(
            calls=len(self.usages),
            input_tokens=sum(
                usage.input_tokens
                for usage in self.usages
            ),
            cached_input_tokens=sum(
                usage.cached_input_tokens
                for usage in self.usages
            ),
            output_tokens=sum(
                usage.output_tokens
                for usage in self.usages
            ),
            total_tokens=sum(
                usage.total_tokens
                for usage in self.usages
            ),
            reasoning_tokens=sum(
                usage.reasoning_tokens
                for usage in self.usages
            ),
            estimated_cost_usd=(
                None
                if any(cost is None for cost in costs)
                else sum(cost for cost in costs if cost is not None)
            ),
            models=tuple(
                sorted(
                    {
                        usage.model
                        for usage in self.usages
                    }
                )
            ),
        )
