from app.wh.runtime.construction_project import ConstructionProject
from app.wh.runtime.construction_schema import ConstructionSchema
from app.wh.runtime.construction_offer import ConstructionOffer
from app.wh.runtime.schema.construction_schema_factory_v2 import (
    ConstructionSchemaFactoryV2
)
from app.wh.runtime.offer_enricher import OfferEnricher
from app.wh.model.opening import Opening
from app.knowledge.constructions.construction_resolver import (
    ConstructionResolver
)


class AgentConstructionCompiler:

    def __init__(
        self,
        offer_enricher=None,
        construction_resolver=None,
        schema_factory=None,
    ):
        self.offer_enricher = (
            offer_enricher
            if offer_enricher is not None
            else OfferEnricher()
        )

        self.construction_resolver = (
            construction_resolver
            if construction_resolver is not None
            else ConstructionResolver()
        )

        self.schema_factory = (
            schema_factory
            if schema_factory is not None
            else ConstructionSchemaFactoryV2()
        )

    def compile(self, context):
        if context.width is None or context.height is None:
            return None

        if context.width <= 0 or context.height <= 0:
            return None

        openings = getattr(
            context,
            "openings",
            (),
        )

        if not openings and context.opening is not None:
            openings = (context.opening,)

        if not openings:
            return None

        pattern = self._resolve_pattern(
            openings
        )

        if pattern is None:
            return None

        schema = self.schema_factory.create(
            pattern=pattern,
            width=context.width,
            height=context.height,
            openings=openings,
        )

        self._normalize_segment_openings(schema)

        offer = self.offer_enricher.enrich(
            context.raw_request
        )

        return ConstructionProject(
            schema=schema,
            offer=offer
        )

    def _resolve_pattern(self, openings):
        construction = self.construction_resolver.resolve(
            list(openings)
        )

        if construction is not None:
            return self._fields_to_pattern(
                construction.fields
            )

        if len(openings) == 1 and openings[0] == "FIX":
            return "FIX"

        return None

    @staticmethod
    def _normalize_segment_openings(schema):
        mapping = {
            "tilt_turn": Opening.TILT_TURN,
            "fix": Opening.FIX,
            "turn": Opening.TURN,
            "tilt": Opening.TILT,
            "psk": Opening.PSK,
            "hst": Opening.HST,
        }

        for segment in schema.segments:
            if isinstance(segment.opening, str):
                segment.opening = mapping.get(
                    segment.opening,
                    segment.opening
                )

    @staticmethod
    def _fields_to_pattern(fields):
        mapping = {
            "RIGHT_TILT_TURN": "RU",
            "LEFT_TILT_TURN": "RU",
            "FIX": "FIX",
        }

        tokens = []

        for field in fields:
            token = mapping.get(field)

            if token is None:
                return None

            tokens.append(token)

        if not tokens:
            return None

        return "|".join(tokens)
