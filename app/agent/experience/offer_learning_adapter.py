"""Bridge normalized offer contexts into privacy-limited learning examples."""

from __future__ import annotations

from app.agent.experience.experience_models import ExperienceFact
from app.agent.experience.guided_learning_service import GuidedLearningSession
from app.agent.offers.offer_context import OfferContext


def facts_from_offer_context(
    context: OfferContext,
) -> tuple[ExperienceFact, ...]:
    """Extract only normalized technical offer fields, never raw customer text."""
    if not isinstance(context, OfferContext):
        raise TypeError("offer_learning_context_invalid")

    values: tuple[tuple[str, object], ...] = (
        ("width", context.width),
        ("height", context.height),
        ("quantity", context.quantity),
        ("product_type", context.product_type),
        ("profile", context.profile),
        ("configuration", context.configuration),
        ("opening", context.opening),
        ("openings", context.openings or None),
        ("color_inside", context.color_inside),
        ("color_outside", context.color_outside),
        ("glazing", context.glazing),
    )
    facts = []
    for key, value in values:
        if value is None:
            continue
        if key == "openings":
            facts.append(ExperienceFact(key=key, value=tuple(value)))
        elif isinstance(value, (str, int)) and not isinstance(value, bool):
            facts.append(ExperienceFact(key=key, value=value))
    return tuple(facts)


def record_offer_context(
    session: GuidedLearningSession,
    context: OfferContext,
) -> tuple[ExperienceFact, ...]:
    """Attach a completed offer's normalized technical facts to a demo session."""
    if not isinstance(session, GuidedLearningSession):
        raise TypeError("offer_learning_session_invalid")
    facts = facts_from_offer_context(context)
    for fact in facts:
        session.record_fact(fact)
    return facts
