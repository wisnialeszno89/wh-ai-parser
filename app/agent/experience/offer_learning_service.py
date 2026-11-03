"""Application-facing facade for teaching NaviMind completed window offers."""

from __future__ import annotations

from app.agent.experience.experience_models import (
    ExperienceEpisode,
    ExperienceStep,
)
from app.agent.experience.experience_store import ExperienceStore
from app.agent.experience.guided_learning_service import (
    GuidedLearningService,
    GuidedLearningSession,
)
from app.agent.experience.offer_learning_adapter import record_offer_context
from app.agent.offers.offer_context import OfferContext


class OfferLearningService:
    """Capture a demonstrated offer workflow and save it after operator approval."""

    def __init__(
        self,
        *,
        store: ExperienceStore,
        tenant_id: str,
        operator_id: str,
    ) -> None:
        self.guided_learning = GuidedLearningService(
            store=store,
            tenant_id=tenant_id,
            operator_id=operator_id,
        )

    def begin_offer_demo(
        self,
        *,
        application_id: str = "okna.exe",
    ) -> GuidedLearningSession:
        return self.guided_learning.begin(
            application_id=application_id,
            task_kind="create_window_offer",
            tags=("window_offer", "create_offer"),
        )

    @staticmethod
    def record_step(
        session: GuidedLearningSession,
        *,
        action: str,
        target: str,
        purpose: str,
        verification: str,
    ) -> None:
        session.record_step(
            ExperienceStep(
                action=action,
                target=target,
                purpose=purpose,
                verification=verification,
            )
        )

    @staticmethod
    def record_final_offer(
        session: GuidedLearningSession,
        context: OfferContext,
    ) -> None:
        record_offer_context(session, context)

    def finish_demo(
        self,
        session: GuidedLearningSession,
        *,
        outcome: str = "completed",
    ) -> ExperienceEpisode:
        return self.guided_learning.complete(session, outcome=outcome)

    def approve_demo(
        self,
        draft: ExperienceEpisode,
        *,
        operator_confirmed: bool,
    ) -> ExperienceEpisode:
        return self.guided_learning.approve(
            draft,
            operator_confirmed=operator_confirmed,
        )
