from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HumanActionEvent:
    """
    Platform-neutral description of one human interaction.

    Physical coordinates may be supplied transiently by a local input
    observer, but are never persisted in the learned workflow.
    """

    action_type: str
    x: int | None = None
    y: int | None = None
    value: str | None = None
    metadata: dict[str, object] | None = None
