from dataclasses import dataclass, field


@dataclass(slots=True)
class AnalysisResult:

    completed: bool = False

    missing: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )