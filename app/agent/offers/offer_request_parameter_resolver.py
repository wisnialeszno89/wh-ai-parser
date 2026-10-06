from __future__ import annotations

from app.agent.agent_request import AgentRequest
from app.agent.learning.learned_parameter import canonical_parameter_name
from app.agent.learning.learned_workflow import LearnedWorkflow
from app.agent.offers.offer_context_parser import OfferContextParser


class OfferRequestParameterResolver:
    """
    Resolve common quotation parameters from a natural-language request.

    This adapter is intentionally outside the Universal Agent core. It turns
    the existing normalized OfferContext into semantic parameter names that
    learned text-entry actions can consume.
    """

    _FIELD_MAP = {
        "width": "width",
        "szerokosc": "width",
        "height": "height",
        "wysokosc": "height",
        "quantity": "quantity",
        "ilosc": "quantity",
        "product_type": "product_type",
        "produkt": "product_type",
        "profile": "profile",
        "profil": "profile",
        "configuration": "configuration",
        "konfiguracja": "configuration",
        "opening": "opening",
        "otwieranie": "opening",
        "glazing": "glazing",
        "szyby": "glazing",
        "kolor_wewnetrzny": "color_inside",
        "kolor_od_srodka": "color_inside",
        "color_inside": "color_inside",
        "kolor_zewnetrzny": "color_outside",
        "kolor_z_zewnatrz": "color_outside",
        "color_outside": "color_outside",
    }

    def __init__(self, parser: OfferContextParser | None = None) -> None:
        self.parser = parser or OfferContextParser()

    def resolve(
        self,
        request: AgentRequest,
        workflow: LearnedWorkflow,
    ) -> dict[str, object]:
        del workflow

        context = self.parser.parse(request.message)

        values = {
            "width": context.width,
            "height": context.height,
            "quantity": context.quantity,
            "product_type": context.product_type,
            "profile": context.profile,
            "configuration": context.configuration,
            "opening": context.opening,
            "glazing": context.glazing,
            "color_inside": context.color_inside,
            "color_outside": context.color_outside,
        }

        resolved = {
            key: value
            for key, value in values.items()
            if value is not None
        }

        # Also publish aliases so labels such as "Szerokość" can be bound
        # without teaching the parameter layer about every surface label.
        for alias, canonical in self._FIELD_MAP.items():
            value = resolved.get(canonical)
            if value is not None:
                resolved.setdefault(alias, value)

        return resolved

    @classmethod
    def parameter_for_label(cls, label: str) -> str | None:
        normalized = canonical_parameter_name(label)
        return cls._FIELD_MAP.get(normalized)
