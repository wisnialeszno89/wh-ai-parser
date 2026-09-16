from app.agent.offers.offer_context import OfferContext
from app.knowledge.constructions.construction_resolver import (
    ConstructionResolver,
)


class OfferConstructionResolver:
    """
    Resolve an agent OfferContext into a technical
    construction definition using Knowledge.
    """

    def __init__(
        self,
        resolver: ConstructionResolver | None = None,
    ):
        self.resolver = (
            resolver or ConstructionResolver()
        )

    def resolve(
        self,
        context: OfferContext,
    ):
        if context.opening is None:
            return None

        return self.resolver.resolve(
            [context.opening]
        )
