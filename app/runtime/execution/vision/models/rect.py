from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Rect:
    """
    Standard rectangle representation used across the Vision Engine.

    Every Vision component should use Rect instead of tuples,
    OpenCV rectangles or WinAPI RECT structures.
    """

    x: int
    y: int
    width: int
    height: int

    @property
    def left(self) -> int:
        return self.x

    @property
    def top(self) -> int:
        return self.y

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def center(self) -> tuple[int, int]:
        return (
            self.x + self.width // 2,
            self.y + self.height // 2,
        )

    @property
    def area(self) -> int:
        return self.width * self.height

    def contains(self, x: int, y: int) -> bool:
        return (
            self.left <= x <= self.right
            and self.top <= y <= self.bottom
        )

    def intersects(self, other: "Rect") -> bool:
        return not (
            self.right < other.left
            or self.left > other.right
            or self.bottom < other.top
            or self.top > other.bottom
        )

    def translate(self, dx: int, dy: int) -> "Rect":
        return Rect(
            x=self.x + dx,
            y=self.y + dy,
            width=self.width,
            height=self.height,
        )