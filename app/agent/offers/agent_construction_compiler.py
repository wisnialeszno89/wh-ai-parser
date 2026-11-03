import re

from app.catalog.profiles import PROFILE_CATALOG
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
        if not self._apply_context_offer_details(offer, context):
            return None

        return ConstructionProject(
            schema=schema,
            offer=offer
        )

    @staticmethod
    def _resolve_color_code(value):
        if not isinstance(value, str) or not value.strip():
            return None

        normalized = value.strip().casefold()
        if normalized in {"white", "biały", "białe", "biała"}:
            # The legacy WindowHub offer model uses an empty color override
            # for the standard white finish.
            return ""
        if normalized in {"anthracite", "antracyt"}:
            return "7016"
        if re.fullmatch(r"\d{4}", normalized):
            return normalized
        return None

    def _apply_context_offer_details(self, offer, context) -> bool:
        """Apply normalized multi-turn context to the legacy offer model."""
        profile_code = getattr(context, "profile", None)
        if profile_code is not None:
            profile_product = PROFILE_CATALOG.get(profile_code)
            if profile_product is None:
                return False
            profile = self.offer_enricher.profile_parser.parse(
                profile_product.name
            )
            if not profile.manufacturer or not profile.system:
                return False
            offer.profile = profile

        glazing = getattr(context, "glazing", None)
        if glazing is not None:
            glass_type = {
                "double": "2glass",
                "triple": "3glass",
            }.get(glazing)
            if glass_type is None:
                return False
            offer.glass.type = glass_type

        for context_field, offer_field in (
            ("color_inside", "color_inside"),
            ("color_outside", "color_outside"),
        ):
            color = getattr(context, context_field, None)
            if color is None:
                continue
            color_code = self._resolve_color_code(color)
            if color_code is None:
                # Do not silently drop an explicitly requested finish.
                return False
            setattr(offer, offer_field, color_code)

        return True

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
