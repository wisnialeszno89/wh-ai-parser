from dataclasses import (
    dataclass
)


@dataclass
class StrategyRecommendation:

    preferred_patterns: list[str]

    risky_patterns: list[str]