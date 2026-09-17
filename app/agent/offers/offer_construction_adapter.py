from app.agent.offers.offer_context import OfferContext as AgentOfferContext
from app.agent.offers.profile_selection import ProfileSelectionSource
from app.context.context_source import ContextSource
from app.context.offer_context import OfferContext as LegacyOfferContext


class OfferConstructionAdapter:

    def adapt(
        self,
        context: AgentOfferContext,
        construction_type: str | None = None,
    ) -> LegacyOfferContext:

        profile, profile_source, manual_review = (
            self._resolve_profile(context)
        )

        return LegacyOfferContext(
            width=context.width,
            height=context.height,
            construction_type=construction_type,
            opening=context.opening,
            color=self._resolve_color(context),
            profile=profile,
            profile_source=profile_source,
            manual_review=manual_review,
        )

    @staticmethod
    def _resolve_profile(
        context: AgentOfferContext,
    ) -> tuple[str | None, ContextSource, bool]:

        if context.profile_source == ProfileSelectionSource.EXPLICIT:
            return (
                context.profile,
                ContextSource.SALESMAN,
                False,
            )

        if context.profile_source == ProfileSelectionSource.UNKNOWN:
            return (
                None,
                ContextSource.DEFAULT,
                True,
            )

        return (
            context.profile,
            ContextSource.DEFAULT,
            False,
        )

    @staticmethod
    def _resolve_color(
        context: AgentOfferContext,
    ) -> str | None:

        if context.color_inside is not None:
            return context.color_inside

        if context.color_outside is not None:
            return context.color_outside

        return None
