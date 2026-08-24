from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.window_model.model import WindowElementType, WindowModel


class WindowChangeType(str, Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"
    UPDATE = "UPDATE"


@dataclass(frozen=True)
class WindowChange:
    change: WindowChangeType
    element_id: str
    element_type: WindowElementType | None = None
    details: dict[str, object] = field(default_factory=dict)


def diff_models(desired: WindowModel, observed: WindowModel) -> list[WindowChange]:
    changes: list[WindowChange] = []

    for element_id, element in desired.elements.items():
        current = observed.elements.get(element_id)
        if current is None:
            changes.append(
                WindowChange(
                    WindowChangeType.ADD,
                    element_id,
                    element.type,
                    {"properties": dict(element.properties), "parent_id": element.parent_id},
                )
            )
            continue
        if current.type != element.type or current.parent_id != element.parent_id or current.properties != element.properties:
            changes.append(
                WindowChange(
                    WindowChangeType.UPDATE,
                    element_id,
                    element.type,
                    {
                        "desired_type": element.type.value,
                        "observed_type": current.type.value,
                        "desired_parent": element.parent_id,
                        "observed_parent": current.parent_id,
                        "desired_properties": dict(element.properties),
                        "observed_properties": dict(current.properties),
                    },
                )
            )

    for element_id, element in observed.elements.items():
        if element_id not in desired.elements:
            changes.append(
                WindowChange(WindowChangeType.REMOVE, element_id, element.type)
            )

    return changes


def build_plan(changes: list[WindowChange]) -> list[str]:
    """Return deterministic semantic steps; execution mapping comes later."""
    steps: list[str] = []
    for item in changes:
        if item.change == WindowChangeType.ADD:
            steps.append(f"ADD {item.element_type.value if item.element_type else 'UNKNOWN'} {item.element_id}")
        elif item.change == WindowChangeType.UPDATE:
            steps.append(f"UPDATE {item.element_type.value if item.element_type else 'UNKNOWN'} {item.element_id}")
        else:
            steps.append(f"REMOVE {item.element_type.value if item.element_type else 'UNKNOWN'} {item.element_id}")
    return steps
