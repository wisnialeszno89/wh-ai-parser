"""Allowed semantic operations for NaviMind task reasoning.

The local runtime must normalize every model-proposed action into this
explicitly supported semantic vocabulary before execution.
"""

NAVIMIND_ALLOWED_ACTIONS = frozenset(
    {
        # Existing WH semantic workflow actions.
        "analyze_request",
        "collect_offer_context",
        "validate_offer",
        "build_construction",
        "prepare_quote",

        # Semantic GUI actions supported by the WindowHub robot bridge.
        "click_screen_element",
        "click",
        "click_ui_element",
        "write_text",
        "type_text",
        "open_new_offer",

        # Semantic browser actions.
        "open_url",
        "read_page",
        "browser_click",
        "browser_write_text",
        "select_option",
        "browser_back",
    }
)

NAVIMIND_ALLOWED_ACTIONS_ORDERED = tuple(
    sorted(NAVIMIND_ALLOWED_ACTIONS)
)
