"""Grounded, bounded WindowHub environment knowledge for local reasoning.

Only statements supported by the observed form map and verified local
acceptance tests; catalog compatibility remains unknown until observed.
This module grants NO UI permissions.
"""
from __future__ import annotations
from app.agent.offers.windowhub_offer_form_map import WINDOWHUB_OFFER_CONTROL_SPECS

STAGE_RULES = {
    "start": ("Start1 is a workspace; NOWA OFERTA starts a NEW offer, not a current-offer edit.",),
    "offer_document": ("OFR/ is an offer. Before Dodaj, verify the selected MDI offer owns that button.",),
    "order_document": ("ZLC/ is an order: READ ONLY. Do not click, type, navigate, save or edit.",),
    "position": ("Choose product type Okno and confirm its radio selection; confirm quantity via native field readback.",),
    "dimensions": ("width_1 and height_1 are overall window dimensions, not segment dimensions. Replace, never append. Verify readback.",),
    "basic_parameters": ("Do not invent a profile, side-specific color or catalog availability.",),
    "glazing": ("The glazing package and spacer are separate catalog choices; check compatibility.",),
    "hardware": ("Opening direction and hardware must be verified against the exact construction.",),
    "modifier": ("Reaching Modyfikator does not prove the requested construction is complete or saved.",),
}

VERIFIED_PATH = ("offer_document", "position", "dimensions")
UNVERIFIED = (
    "Full offer creation from any arbitrary WindowHub screen",
    "Catalog compatibility and available profiles",
    "Autonomous customer selection and offer finalization",
    "End-to-end AI-driven live execution",
)

def windowhub_environment_knowledge(stage: str | None = None) -> dict[str, object]:
    known = sorted({spec.step.value for spec in WINDOWHUB_OFFER_CONTROL_SPECS})
    fields = [
        {"stage": spec.step.value, "field": spec.field_name,
         "control": spec.control_type, "label": spec.label}
        for spec in WINDOWHUB_OFFER_CONTROL_SPECS
        if stage is None or spec.step.value == stage
    ]
    return {
        "source": "observed_windowhub_form_map_and_local_acceptance",
        "version": 1,
        "stage": stage or "all",
        "document_policy": {
            "OFR/": "verified offer document; edits limited to locally checked skills",
            "ZLC/": "read_only_no_mutations",
            "unknown": "read_only_until_classified",
        },
        "verified_workflow": list(VERIFIED_PATH),
        "rules": list(STAGE_RULES.get(stage, (
            "Observe current stage first; do not assume the requested wizard is active.",
        ))),
        "mapped_field_count": len(fields),
        "fields": fields[:60],
        "unverified": list(UNVERIFIED),
        "permissions": "knowledge_only_never_grants_execution",
    }
