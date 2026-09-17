from app.agent.offers.offer_construction_adapter import (
    OfferConstructionAdapter,
)
from app.agent.offers.offer_construction_resolver import (
    OfferConstructionResolver,
)
from app.agent.offers.offer_context import (
    OfferContext,
)
from app.construction.construction_builder import (
    ConstructionBuilder,
)


class OfferConstructionService:

    def __init__(
        self,
        resolver: OfferConstructionResolver | None = None,
        adapter: OfferConstructionAdapter | None = None,
        builder: ConstructionBuilder | None = None,
    ):
        self.resolver = (
            resolver
            if resolver is not None
            else OfferConstructionResolver()
        )

        self.adapter = (
            adapter
            if adapter is not None
            else OfferConstructionAdapter()
        )

        self.builder = (
            builder
            if builder is not None
            else ConstructionBuilder()
        )

    def build(
        self,
        context: OfferContext,
    ):
        construction_definition = self.resolver.resolve(
            context
        )

        if construction_definition is None:
            return None

        legacy_context = self.adapter.adapt(
            context,
            construction_type=construction_definition.code,
        )

        return self.builder.build(
            legacy_context
        )
