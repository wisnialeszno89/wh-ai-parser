"""Typed, provider-neutral queries for semantic screen targets.

Queries are constructed by local skills/adapters. Provider identifiers remain
local and are never part of NaviMind's public task contract.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


def _optional_text(value: str | None, field_name: str) -> None:
    if value is not None and (
        not isinstance(value, str) or not value.strip()
    ):
        raise ValueError(f"semantic_target_{field_name}_invalid")


@dataclass(frozen=True)
class SemanticAncestorConstraint:
    """Require a target to be contained by an ancestor with these properties."""

    control_type: str | None = None
    class_name: str | None = None
    automation_id: str | None = None
    name: str | None = None

    def __post_init__(self) -> None:
        values = (
            self.control_type,
            self.class_name,
            self.automation_id,
            self.name,
        )
        for name, value in zip(
            ("control_type", "class_name", "automation_id", "name"),
            values,
        ):
            _optional_text(value, name)
        if not any(value is not None for value in values):
            raise ValueError("semantic_ancestor_constraint_empty")

    def matches(self, candidate: object) -> bool:
        if not isinstance(candidate, Mapping):
            return False

        for key, expected in (
            ("control_type", self.control_type),
            ("class_name", self.class_name),
            ("automation_id", self.automation_id),
            ("name", self.name),
        ):
            if expected is None:
                continue
            actual = candidate.get(key)
            if (
                not isinstance(actual, str)
                or actual.strip().casefold() != expected.strip().casefold()
            ):
                return False

        return True


@dataclass(frozen=True)
class SemanticTargetQuery:
    """A deterministic semantic target query; it never contains coordinates."""

    role: str | None = None
    label: str | None = None
    automation_id: str | None = None
    within: SemanticAncestorConstraint | None = None
    description: str = "semantic target"

    def __post_init__(self) -> None:
        values = (
            ("role", self.role),
            ("label", self.label),
            ("automation_id", self.automation_id),
            ("description", self.description),
        )
        for field_name, value in values:
            _optional_text(value, field_name)

        if not any(
            value is not None
            for value in (self.role, self.label, self.automation_id)
        ):
            raise ValueError("semantic_target_query_has_no_selector")
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("semantic_target_description_invalid")
        if self.within is not None and not isinstance(
            self.within,
            SemanticAncestorConstraint,
        ):
            raise TypeError("semantic_target_within_invalid")
