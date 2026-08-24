from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WindowElementType(str, Enum):
    FRAME = "FRAME"
    SASH = "SASH"
    GLASS = "GLASS"
    MULLION = "MULLION"
    HORIZONTAL_MULLION = "HORIZONTAL_MULLION"
    MOVABLE_MULLION = "MOVABLE_MULLION"
    HARDWARE = "HARDWARE"
    CONNECTOR = "CONNECTOR"
    LIMITER = "LIMITER"


class WindowRelationType(str, Enum):
    CONTAINS = "CONTAINS"
    BELONGS_TO = "BELONGS_TO"
    INSTALLED_ON = "INSTALLED_ON"
    INSIDE = "INSIDE"
    DIVIDES = "DIVIDES"
    ADJACENT_TO = "ADJACENT_TO"


@dataclass(frozen=True)
class WindowRelation:
    source_id: str
    relation: WindowRelationType
    target_id: str


@dataclass
class WindowElement:
    id: str
    type: WindowElementType
    parent_id: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class WindowModel:
    """Canonical semantic model of a window independent of WindowHub UI."""

    id: str = "window"
    properties: dict[str, Any] = field(default_factory=dict)
    elements: dict[str, WindowElement] = field(default_factory=dict)
    relations: list[WindowRelation] = field(default_factory=list)

    def add_element(
        self,
        element_id: str,
        element_type: WindowElementType,
        *,
        parent_id: str | None = None,
        **properties: Any,
    ) -> WindowElement:
        if element_id in self.elements:
            raise ValueError(f"Element already exists: {element_id}")
        if parent_id is not None and parent_id not in self.elements and parent_id != self.id:
            raise ValueError(f"Parent element does not exist: {parent_id}")
        element = WindowElement(
            id=element_id,
            type=element_type,
            parent_id=parent_id,
            properties=dict(properties),
        )
        self.elements[element_id] = element
        if parent_id is not None:
            self.add_relation(parent_id, WindowRelationType.CONTAINS, element_id)
        return element

    def add_relation(
        self,
        source_id: str,
        relation: WindowRelationType,
        target_id: str,
    ) -> WindowRelation:
        valid_ids = {self.id, *self.elements.keys()}
        if source_id not in valid_ids:
            raise ValueError(f"Unknown source element: {source_id}")
        if target_id not in valid_ids:
            raise ValueError(f"Unknown target element: {target_id}")
        item = WindowRelation(source_id, relation, target_id)
        if item not in self.relations:
            self.relations.append(item)
        return item

    def children_of(self, parent_id: str) -> list[WindowElement]:
        return [e for e in self.elements.values() if e.parent_id == parent_id]

    def elements_of_type(self, element_type: WindowElementType) -> list[WindowElement]:
        return [e for e in self.elements.values() if e.type == element_type]

    def has_type(self, element_type: WindowElementType) -> bool:
        return any(e.type == element_type for e in self.elements.values())

    def validate(self) -> list[str]:
        errors: list[str] = []
        frames = self.elements_of_type(WindowElementType.FRAME)
        if len(frames) > 1:
            errors.append("WindowModel currently supports one root FRAME")

        for element in self.elements.values():
            if element.parent_id == element.id:
                errors.append(f"Element cannot parent itself: {element.id}")

        for relation in self.relations:
            if relation.source_id not in {self.id, *self.elements.keys()}:
                errors.append(f"Unknown relation source: {relation.source_id}")
            if relation.target_id not in {self.id, *self.elements.keys()}:
                errors.append(f"Unknown relation target: {relation.target_id}")

        for sash in self.elements_of_type(WindowElementType.SASH):
            if sash.parent_id is None:
                errors.append(f"SASH requires a containing cell/frame: {sash.id}")

        for glass in self.elements_of_type(WindowElementType.GLASS):
            if glass.parent_id is None:
                errors.append(f"GLASS requires a containing sash/cell: {glass.id}")

        for hardware in self.elements_of_type(WindowElementType.HARDWARE):
            if hardware.parent_id is None:
                errors.append(f"HARDWARE requires an owner sash/frame: {hardware.id}")

        return errors
