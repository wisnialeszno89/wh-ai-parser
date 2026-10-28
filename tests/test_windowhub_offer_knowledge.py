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


def test_new_offer_navigation_respects_active_document_scope():
    knowledge = get_windowhub_offer_knowledge()
    start_stage = knowledge["workflow"][0]
    sequence = " ".join(start_stage["preferred_action_sequence"])
    rules = " ".join(knowledge["safety_rules"])

    assert "Start1" in sequence
    assert "active document" in sequence
    assert "re-observe" in sequence
    assert "document_scope conflicts" in rules
    assert "never bypass the document-scope guard" in rules


def test_windowhub_interface_guide_distinguishes_new_offers_from_other_workflows():
    knowledge = get_windowhub_offer_knowledge()
    guide = knowledge["interface_guide"]
    controls = {item["label"]: item for item in guide["controls"]}

    assert "Start1" in controls
    assert "NOWA OFERTA" in controls
    assert "ISTNIEJĄCE DOKUMENTY" in controls
    assert "NOWE ZLECENIE" in controls
    assert "NOWE ZAMÓWIENIE" in controls

    assert "new quotation" in controls["NOWA OFERTA"]["meaning"]
    assert "Starting a new quotation" not in controls["ISTNIEJĄCE DOKUMENTY"]["meaning"]
    assert "Starting a new quotation" not in controls["NOWE ZLECENIE"]["meaning"]
    assert "Re-observe" in controls["Start1"]["after_action"]
    assert "scope conflicts with the active document" in controls["NOWA OFERTA"]["avoid_when"]


def test_windowhub_interface_guide_labels_evidence_and_uncertain_icon_semantics():
    knowledge = get_windowhub_offer_knowledge()
    guide = knowledge["interface_guide"]
    policy = " ".join(guide["icon_learning_policy"])
    controls = {item["label"]: item for item in guide["controls"]}

    assert "do not guess its meaning" in policy
    assert "before/after" in policy
    assert "screen coordinates" in policy
    assert "AutomationId" in policy
    assert "exact visible glyph not independently identified" in controls["Undo"]["evidence"]
    assert "save/persist data" in controls["Zachowaj"]["risk"]
    assert "occurs more than once" in controls["Otwórz"]["use_when"]


def test_windowhub_interface_guide_is_json_serializable_for_task_reasoners():
    import json

    knowledge = get_windowhub_offer_knowledge()
    payload = json.dumps(knowledge, ensure_ascii=False)

    assert '"interface_guide"' in payload
    assert '"NOWA OFERTA"' in payload
    assert '"icon_learning_policy"' in payload


def test_windowhub_navigation_requires_observed_state_change_not_just_click_success():
    knowledge = get_windowhub_offer_knowledge()
    start_sequence = " ".join(
        knowledge["workflow"][0]["preferred_action_sequence"]
    )
    safety_rules = " ".join(knowledge["safety_rules"])

    assert "guarded MDI activation path" in start_sequence
    assert "verifies the active MDI document, and checks UIA selected state when available" in start_sequence
    assert "as proof of navigation" in start_sequence
    assert "stop for review rather than retrying a generic coordinate click" in safety_rules
