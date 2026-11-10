from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SceneElement:
    id: str
    kind: str
    parent_id: str | None = None
    side: str | None = None
    opening: str | None = None
    direction: str | None = None
    inversion_checked: bool | None = None
    offset_from_left_mm: int | None = None
    panes: int | None = None
    swing: str | None = None


@dataclass
class WindowScene:
    """Small deterministic state model for agent development away from WH."""

    width: int = 1000
    height: int = 1000
    elements: list[SceneElement] = field(default_factory=list)

    def has(self, kind: str, *, side: str | None = None) -> bool:
        return any(
            item.kind == kind and (side is None or item.side == side)
            for item in self.elements
        )

    def add(self, element: SceneElement) -> None:
        if any(item.id == element.id for item in self.elements):
            raise ValueError(f"duplicate element id: {element.id}")
        if element.parent_id and not any(item.id == element.parent_id for item in self.elements):
            raise ValueError(f"missing parent: {element.parent_id}")
        self.elements.append(element)

    def kinds(self) -> tuple[str, ...]:
        return tuple(item.kind for item in self.elements)

    def semantic_snapshot(self) -> dict:
        return {
            "opening": {"width": self.width, "height": self.height},
            "elements": [
                {
                    "id": item.id,
                    "kind": item.kind,
                    "parent_id": item.parent_id,
                    "side": item.side,
                    **({"opening": item.opening, "direction": item.direction} if item.opening is not None else {}),
                    **({"inversion_checked": item.inversion_checked} if item.inversion_checked is not None else {}),
                    **({"offset_from_left_mm": item.offset_from_left_mm} if item.offset_from_left_mm is not None else {}),
                    **({"panes": item.panes} if item.panes is not None else {}),
                    **({"swing": item.swing} if item.swing is not None else {}),
                }
                for item in self.elements
            ],
        }

    @classmethod
    def empty(cls, width: int = 1000, height: int = 1000) -> "WindowScene":
        return cls(width=width, height=height)
