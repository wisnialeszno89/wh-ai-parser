from app.wh.model.opening import Opening
from app.wh.runtime.construction_project import ConstructionProject
from app.wh.runtime.construction_schema import ConstructionSchema
from app.wh.runtime.construction_offer import ConstructionOffer
from app.wh.runtime.segments.segment import Segment
from app.wh.runtime.offer_enricher import OfferEnricher


class AgentConstructionCompiler:

    def __init__(self, offer_enricher=None):
        self.offer_enricher = (
            offer_enricher
            if offer_enricher is not None
            else OfferEnricher()
        )

    def compile(self, context):
        if context.width is None or context.height is None:
            return None

        if context.width <= 0 or context.height <= 0:
            return None

        if context.opening is None:
            return None

        opening = self._resolve_opening(context.opening)

        if opening is None:
            return None

        schema = ConstructionSchema(
            width=context.width,
            height=context.height,
            schema=opening.value,
            segments=[
                Segment(
                    opening=opening
                )
            ]
        )

        offer = self.offer_enricher.enrich(
            context.raw_request
        )

        return ConstructionProject(
            schema=schema,
            offer=offer
        )

    @staticmethod
    def _resolve_opening(opening):
        mapping = {
            "FIX": Opening.FIX,
            "RIGHT_TILT_TURN": Opening.TILT_TURN,
            "LEFT_TILT_TURN": Opening.TILT_TURN,
            "TILT_TURN": Opening.TILT_TURN,
            "TURN": Opening.TURN,
            "TILT": Opening.TILT,
            "PSK": Opening.PSK,
            "HST": Opening.HST,
        }

        return mapping.get(opening)
