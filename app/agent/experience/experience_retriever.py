"""Bounded retrieval of operator-approved workflow examples."""

from __future__ import annotations

import re

from app.agent.experience.experience_store import ExperienceStore


class ExperienceRetriever:
    """Retrieve examples only for the configured company/operator/application."""

    def __init__(
        self,
        *,
        store: ExperienceStore,
        tenant_id: str,
        operator_id: str,
    ) -> None:
        self.store = store
        self.tenant_id = tenant_id.strip().casefold()
        self.operator_id = operator_id.strip().casefold()
        if not self.tenant_id or not self.operator_id:
            raise ValueError("experience_retriever_scope_required")

    def retrieve(
        self,
        *,
        application_id: str,
        goal: str,
        max_items: int = 3,
    ) -> tuple[dict[str, object], ...]:
        if isinstance(max_items, bool) or not 1 <= max_items <= 5:
            raise ValueError("experience_retrieval_limit_invalid")
        if not isinstance(application_id, str) or not application_id.strip():
            return ()
        episodes = self.store.list_approved(
            tenant_id=self.tenant_id,
            operator_id=self.operator_id,
            application_id=application_id.strip().casefold(),
        )
        if not episodes:
            return ()

        terms = {
            token.casefold()
            for token in re.findall(r"[a-zA-Z0-9_.-]{2,}", goal or "")
        } if isinstance(goal, str) else set()

        def score(episode) -> tuple[int, str]:
            known_values = (
                *episode.tags,
                episode.task_kind,
                *(step.target for step in episode.steps),
            )
            known = {
                token.casefold()
                for value in known_values
                for token in re.findall(r"[a-zA-Z0-9_.-]{2,}", value)
            }
            overlap = len(terms.intersection(known))
            return overlap, episode.created_at_utc

        ranked = sorted(episodes, key=score, reverse=True)
        return tuple(
            episode.to_prompt_payload()
            for episode in ranked[:max_items]
        )
