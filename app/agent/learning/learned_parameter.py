from __future__ import annotations

import re
import unicodedata
from dataclasses import replace
from collections.abc import Mapping

from app.agent.learning.learned_workflow import LearnedAction


def canonical_parameter_name(label: str) -> str:
    """
    Convert a semantic field label into a stable parameter key.

    The key is derived only from the semantic label, never from coordinates
    or runtime/provider identifiers.
    """
    normalized = unicodedata.normalize("NFKD", label)
    ascii_text = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    ascii_text = ascii_text.casefold()
    ascii_text = re.sub(r"[^a-z0-9]+", "_", ascii_text).strip("_")
    return ascii_text


class LearnedParameterBinder:
    """
    Apply request-time semantic parameters to learned actions.

    A parameterized action keeps its demonstrated value as a safe fallback.
    When a matching parameter is supplied, that value overrides the demo
    value for the current replay only.
    """

    def bind(
        self,
        action: LearnedAction,
        parameters: Mapping[str, object] | None = None,
    ) -> LearnedAction:
        if (
            action.value_source != "parameter"
            or not action.parameter_name
            or parameters is None
        ):
            return action

        parameter_name = canonical_parameter_name(
            action.parameter_name
        )

        for key, value in parameters.items():
            if canonical_parameter_name(str(key)) != parameter_name:
                continue

            if value is None:
                return action

            return replace(
                action,
                value=str(value),
            )

        return action
