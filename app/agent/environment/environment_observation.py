from dataclasses import dataclass, field

from app.agent.environment.environment_state import (
    EnvironmentState,
)


@dataclass(frozen=True)
class EnvironmentObservation:
    """
    Snapshot of the environment observed by the agent.

    The observation is intentionally immutable.

    Later perception systems may enrich this model with:
    - screenshots
    - detected UI elements
    - OCR results
    - scene information
    - confidence scores
    """

    state: EnvironmentState

    metadata: dict[str, object] = field(
        default_factory=dict
    )
