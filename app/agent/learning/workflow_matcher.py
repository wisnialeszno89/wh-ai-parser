from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.agent.learning.learned_workflow import LearnedWorkflow


@dataclass(frozen=True)
class WorkflowMatch:
    """Ranked semantic match between a request and a learned workflow."""

    workflow: LearnedWorkflow
    score: float
    reasons: tuple[str, ...] = ()


class WorkflowMatcher:
    """Find learned procedures from natural-language requests.

    The first implementation is deliberately deterministic. It creates a
    stable retrieval contract that can later be replaced or augmented by
    embeddings without changing the rest of the runtime.
    """

    _TOKEN_RE = re.compile(r"[a-z0-9ąćęłńóśźżäöüß]+", re.IGNORECASE)

    def match(
        self,
        message: str,
        workflows: tuple[LearnedWorkflow, ...],
        *,
        application: str | None = None,
        limit: int = 5,
        min_score: float = 0.55,
    ) -> tuple[WorkflowMatch, ...]:
        if not isinstance(message, str) or not message.strip():
            return ()
        if limit < 1:
            raise ValueError("limit must be positive.")
        if not 0.0 <= min_score <= 1.0:
            raise ValueError("min_score must be between 0 and 1.")

        normalized_message = self._normalize(message)
        message_tokens = self._tokens(normalized_message)

        matches: list[WorkflowMatch] = []
        for workflow in workflows:
            if application is not None:
                if (
                    workflow.application is None
                    or workflow.application.strip().casefold()
                    != application.strip().casefold()
                ):
                    continue

            trigger = self._normalize(workflow.trigger)
            name = self._normalize(workflow.name)
            trigger_tokens = self._tokens(trigger)
            name_tokens = self._tokens(name)

            score, reasons = self._score(
                normalized_message,
                message_tokens,
                trigger,
                trigger_tokens,
                name_tokens,
            )

            if score >= min_score:
                matches.append(
                    WorkflowMatch(
                        workflow=workflow,
                        score=score,
                        reasons=tuple(reasons),
                    )
                )

        matches.sort(
            key=lambda item: (
                -item.score,
                item.workflow.name.casefold(),
                item.workflow.workflow_id,
            )
        )
        return tuple(matches[:limit])

    def best_match(
        self,
        message: str,
        workflows: tuple[LearnedWorkflow, ...],
        *,
        application: str | None = None,
        min_score: float = 0.55,
    ) -> WorkflowMatch | None:
        matches = self.match(
            message,
            workflows,
            application=application,
            min_score=min_score,
            limit=1,
        )
        return matches[0] if matches else None

    @classmethod
    def _score(
        cls,
        normalized_message: str,
        message_tokens: set[str],
        trigger: str,
        trigger_tokens: set[str],
        name_tokens: set[str],
    ) -> tuple[float, list[str]]:
        if normalized_message == trigger and trigger:
            return 1.0, ["exact_trigger"]

        if trigger and (
            trigger in normalized_message
            or normalized_message in trigger
        ):
            return 0.92, ["trigger_substring"]

        if not trigger_tokens:
            return 0.0, []

        overlap = len(message_tokens & trigger_tokens)
        union = len(message_tokens | trigger_tokens)
        jaccard = overlap / union if union else 0.0

        name_overlap = len(message_tokens & name_tokens)
        name_ratio = (
            name_overlap / len(message_tokens)
            if message_tokens and name_tokens
            else 0.0
        )

        score = min(
            1.0,
            (jaccard * 0.8) + (name_ratio * 0.2),
        )

        reasons: list[str] = []
        if overlap:
            reasons.append("trigger_token_overlap")
        if name_overlap:
            reasons.append("workflow_name_overlap")

        return score, reasons

    @classmethod
    def _normalize(cls, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.casefold())
        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )
        return " ".join(normalized.split())

    @classmethod
    def _tokens(cls, value: str) -> set[str]:
        return set(cls._TOKEN_RE.findall(value))
