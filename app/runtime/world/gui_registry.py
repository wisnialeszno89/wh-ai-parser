from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GuiDefinition:
    """Static GUI definition used by runtime perception helpers."""

    name: str
    region: str
    template: str | None = None
    confidence: float = 0.0


FRAME_WIDTH = GuiDefinition(
    name="FRAME_WIDTH",
    region="RIGHT_PANEL",
    template="frame_width.png",
    confidence=0.92,
)


__all__ = ["GuiDefinition", "FRAME_WIDTH"]
