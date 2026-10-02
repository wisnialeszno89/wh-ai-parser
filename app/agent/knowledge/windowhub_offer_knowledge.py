from __future__ import annotations


WINDOWHUB_OFFER_KNOWLEDGE: dict[str, object] = {
    "application": "WindowHub",
    "purpose": (
        "Guide safe semantic navigation of the WindowHub quotation workflow. "
        "The model must use the current visible scene as the source of truth "
        "for actual controls."
    ),
    "workflow": (
        {
            "stage": 1,
            "name": "start_new_offer",
            "goal": "Start a new quotation.",
            "expected_visible_controls": ("Nowa oferta",),
            "typical_next_action": "click_screen_element",
        },
        {
            "stage": 2,
            "name": "customer_and_preferences",
            "goal": (
                "Complete the new-offer dialog with customer and valuation "
                "preferences, then confirm it."
            ),
            "expected_visible_controls": ("OK", "Anuluj"),
            "preferred_action_sequence": (
                "write required customer/preferences fields",
                "click OK",
            ),
        },
        {
            "stage": 3,
            "name": "position_type",
            "goal": "Add the quotation position and choose a window.",
            "expected_semantic_targets": (
                "Dodaj artykuł do konstrukcji",
                "okno",
                "OK",
            ),
            "preferred_action_sequence": (
                "open position/item selector",
                "choose visible window product",
                "click OK",
            ),
        },
        {
            "stage": 4,
            "name": "dimensions",
            "goal": "Enter the requested width and height.",
            "field_roles": (
                "width",
                "height",
            ),
            "preferred_action_sequence": (
                "write width",
                "write height",
                "click OK",
            ),
        },
        {
            "stage": 5,
            "name": "basic_window_parameters",
            "goal": "Set basic window parameters such as colour.",
            "field_roles": (
                "colour",
                "glazing",
                "opening",
            ),
            "preferred_action_sequence": (
                "write/select requested values",
                "click Zakończ",
            ),
        },
        {
            "stage": 6,
            "name": "construction_editor",
            "goal": (
                "Work with the actual construction editor only after the "
                "basic parameter stage has been completed."
            ),
            "preferred_action_sequence": (
                "observe construction-specific controls",
                "choose only controls supported by the visible scene",
                "verify after each mutation",
            ),
        },
    ),
    "field_synonyms": {
        "customer": (
            "klient",
            "kontrahent",
            "odbiorca",
            "nabywca",
        ),
        "width": (
            "szerokość",
            "szer",
            "width",
        ),
        "height": (
            "wysokość",
            "wys",
            "height",
        ),
        "quantity": (
            "ilość",
            "liczba",
            "sztuk",
            "sztuki",
        ),
        "colour": (
            "kolor",
            "barwa",
            "RAL",
        ),
        "glazing": (
            "szyba",
            "szklenie",
            "pakiet szybowy",
        ),
        "opening": (
            "otwarcie",
            "otwieranie",
            "skrzydło",
            "FIX",
        ),
    },
    "safety_rules": (
        "Never use coordinates or internal UIA identifiers as model targets.",
        "Never restart a continuation with Nowa oferta.",
        "Never choose a generic LayoutItem when a semantic field label cannot "
        "be established from UIA structure or other evidence.",
        "Prefer one small GUI mutation at a time and re-observe after it.",
        "Never infer a field solely from ordinal position when multiple "
        "controls are ambiguous.",
        "Use visible OK or Anuluj only when those controls are actually "
        "present in the current scene.",
        "Business data supplied by the salesperson is authoritative; do not "
        "invent missing commercial choices.",
    ),
    "semantic_perception": (
        "WindowHub uses DevExpress WPF layout controls. Generic UIA names "
        "such as LayoutItem can wrap labelled editors. Resolve the semantic "
        "field from parent/child relationships, nearby text labels, and "
        "supported UI Automation properties before exposing it to the "
        "reasoner."
    ),
}


def get_windowhub_offer_knowledge() -> dict[str, object]:
    return WINDOWHUB_OFFER_KNOWLEDGE
