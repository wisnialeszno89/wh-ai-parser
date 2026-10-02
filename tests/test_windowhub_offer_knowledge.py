from app.agent.knowledge.windowhub_offer_knowledge import (
    get_windowhub_offer_knowledge,
)


def test_windowhub_offer_knowledge_contains_safe_workflow():
    knowledge = get_windowhub_offer_knowledge()

    assert knowledge["application"] == "WindowHub"

    stages = knowledge["workflow"]

    assert stages[0]["name"] == "start_new_offer"
    assert stages[1]["name"] == "customer_and_preferences"
    assert stages[2]["name"] == "position_type"
    assert stages[3]["name"] == "dimensions"
    assert stages[4]["name"] == "basic_window_parameters"
    assert stages[5]["name"] == "construction_editor"


def test_windowhub_offer_knowledge_forbids_guessing_generic_layout_items():
    knowledge = get_windowhub_offer_knowledge()

    rules = knowledge["safety_rules"]

    assert any(
        "generic LayoutItem" in rule
        for rule in rules
    )
    assert any(
        "ordinal position" in rule
        for rule in rules
    )
