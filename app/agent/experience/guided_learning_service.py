"""Guided demonstration capture with an explicit operator approval gate."""

from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses import replace
from uuid import uuid4

from app.agent.experience.experience_models import (
    ExperienceEpisode,
    ExperienceStep,
)
from app.agent.experience.experience_store import ExperienceStore


@dataclass
class GuidedLearningSession:
    """In-memory draft of one operator-demonstrated application workflow."""

    tenant_id: str
    operator_id: str
    application_id: str
    task_kind: str
    tags: tuple[str, ...]
    session_id: str = field(default_factory=lambda: uuid4().hex)
    steps: list[ExperienceStep] = field(default_factory=list)
    closed: bool = False

    def record_step(self, step: ExperienceStep) -> None:
        if self.closed:
            raise ValueError("guided_learning_session_closed")
        if not isinstance(step, ExperienceStep):
            raise TypeError("guided_learning_step_invalid")
        if len(self.steps) >= 60:
            raise ValueError("guided_learning_step_limit_reached")
        self.steps.append(step)


class GuidedLearningService:
    """Record demonstrations, then save them only after operator review."""

    def __init__(
        self,
        *,
        store: ExperienceStore,
        tenant_id: str,
        operator_id: str,
    ) -> None:
        if not isinstance(store, ExperienceStore):
            raise TypeError("guided_learning_store_invalid")
        self.store = store
        self.tenant_id = tenant_id.strip().casefold()
        self.operator_id = operator_id.strip().casefold()
        if not self.tenant_id or not self.operator_id:
            raise ValueError("guided_learning_scope_required")

    def begin(
        self,
        *,
        application_id: str,
        task_kind: str,
        tags: tuple[str, ...] = (),
    ) -> GuidedLearningSession:
        return GuidedLearningSession(
            tenant_id=self.tenant_id,
            operator_id=self.operator_id,
            application_id=application_id.strip().casefold(),
            task_kind=task_kind.strip().casefold(),
            tags=tags,
        )

    def complete(
        self,
        session: GuidedLearningSession,
        *,
        outcome: str,
    ) -> ExperienceEpisode:
        if not isinstance(session, GuidedLearningSession):
            raise TypeError("guided_learning_session_invalid")
        if session.closed:
            raise ValueError("guided_learning_session_closed")
        if (
            session.tenant_id != self.tenant_id
            or session.operator_id != self.operator_id
        ):
            raise ValueError("guided_learning_scope_mismatch")
        if not session.steps:
            raise ValueError("guided_learning_steps_required")
        draft = ExperienceEpisode(
            tenant_id=session.tenant_id,
            operator_id=session.operator_id,
            application_id=session.application_id,
            task_kind=session.task_kind,
            tags=session.tags,
            steps=tuple(session.steps),
            outcome=outcome,
            approved_by_operator=False,
        )
        session.closed = True
        return draft

    def approve(
        self,
        draft: ExperienceEpisode,
        *,
        operator_confirmed: bool,
    ) -> ExperienceEpisode:
        if operator_confirmed is not True:
            raise ValueError("guided_learning_operator_approval_required")
        if not isinstance(draft, ExperienceEpisode):
            raise TypeError("guided_learning_draft_invalid")
        if (
            draft.tenant_id != self.tenant_id
            or draft.operator_id != self.operator_id
        ):
            raise ValueError("guided_learning_scope_mismatch")
        if draft.approved_by_operator:
            raise ValueError("guided_learning_draft_already_approved")
        approved = replace(draft, approved_by_operator=True)
        return self.store.save_approved(approved)
