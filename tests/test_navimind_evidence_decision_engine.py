from app.agent.reasoning.navimind_evidence_decision_engine import (
    ActionOption, DecisionContext, KnowledgeFact, NextStep, SourceKind,
    plan_next_step, validate_model_proposal,
)


def ctx(**kwargs):
    parameters = dict(
        goal="Create unsaved quotation for requested customer",
        stage="dimensions",
        exact_document_verified=True,
        observation_fresh=True,
        requested_result_verified=False,
        capabilities=(),
    )
    parameters.update(kwargs)
    return DecisionContext(**parameters)


def option(key="write:width", **kwargs):
    params = dict(key=key, target="width_1", expected_result="field_equal",
                  available=True, unique_target=True)
    params.update(kwargs)
    return ActionOption(**params)


def test_stop_for_order_and_unknown_application():
    assert plan_next_step(ctx(stage="order_document")).kind == NextStep.STOP
    assert plan_next_step(ctx(stage="windowhub_unmapped")).kind == NextStep.STOP


def test_reobserve_before_action_if_document_or_scene_unknown():
    assert plan_next_step(ctx(exact_document_verified=False, capabilities=(option(),))).kind == NextStep.OBSERVE
    assert plan_next_step(ctx(observation_fresh=False, capabilities=(option(),))).kind == NextStep.OBSERVE


def test_completion_requires_external_postcondition():
    assert plan_next_step(ctx(requested_result_verified=True)).kind == NextStep.COMPLETE
    assert plan_next_step(ctx(requested_result_verified=False)).kind != NextStep.COMPLETE


def test_one_safe_unique_action_is_planned():
    result = plan_next_step(ctx(capabilities=(option(),)))
    assert result.kind == NextStep.ACT
    assert result.action_key == "write:width"


def test_no_blind_repeat_after_unchanged_scene():
    result = plan_next_step(ctx(capabilities=(option(),), attempted_without_progress=("write:width",)))
    assert result.kind == NextStep.ASK
    assert result.action_key is None


def test_persistence_never_autonomous_even_with_generic_approval():
    result = plan_next_step(ctx(
        human_approval=True,
        capabilities=(option("save", persists_business_document=True),),
    ))
    assert result.kind == NextStep.ASK


def test_missing_technical_fact_triggers_consult():
    result = plan_next_step(ctx(
        pending_unknowns=("hardware_compatibility",),
        capabilities=(option("hardware:set"),),
    ))
    assert result.kind == NextStep.CONSULT
    assert result.unresolved == ("hardware_compatibility",)


def test_public_web_and_model_guess_cannot_satisfy_verified_technical_fact():
    for kind in (SourceKind.PUBLIC_WEB, SourceKind.MODEL_INFERENCE):
        fact = KnowledgeFact("hardware_compatibility", "yes", kind, "web", verified=True)
        result = plan_next_step(ctx(
            pending_unknowns=("hardware_compatibility",),
            knowledge=(fact,),
            capabilities=(option("hardware:set", documentation_key="hardware_compatibility"),),
        ))
        assert result.kind == NextStep.CONSULT


def test_verified_supplier_doc_supports_intent_not_ui_postcondition():
    fact = KnowledgeFact("profile_rule", "compatible", SourceKind.WINKHAUS_DOC,
                         "manual-section-3", verified=True)
    result = plan_next_step(ctx(
        pending_unknowns=("profile_rule",),
        knowledge=(fact,),
        capabilities=(option("choose:profile", documentation_key="profile_rule"),),
    ))
    assert result.kind == NextStep.ACT
    assert result.evidence_keys == ("profile_rule",)


def test_catalogue_inspection_before_escalation():
    result = plan_next_step(ctx(
        pending_unknowns=("color_availability",),
        capabilities=(option("inspect:catalogue"),),
    ))
    assert result.kind == NextStep.ACT
    assert result.action_key == "inspect:catalogue"


def test_multiple_visible_options_require_ranking_not_first_entry():
    result = plan_next_step(ctx(capabilities=(option("click:first"), option("click:second"))))
    assert result.kind == NextStep.OBSERVE
    assert result.action_key is None


def test_ambiguous_unavailable_or_confirmation_action_never_guessed():
    result = plan_next_step(ctx(capabilities=(option(unique_target=False),)))
    assert result.kind == NextStep.ASK
    assert plan_next_step(ctx(capabilities=(option(requires_approval=True),))).kind == NextStep.ASK


def test_model_can_rank_multiple_safe_options_but_not_invent_target():
    context = ctx(capabilities=(option("click:one"), option("click:two")))
    result = validate_model_proposal(context, "click:two")
    assert result.kind == NextStep.ACT
    assert result.action_key == "click:two"
    assert validate_model_proposal(context, "click:three").kind == NextStep.OBSERVE


def test_model_cannot_override_unsafe_save_or_replayed_action():
    assert validate_model_proposal(ctx(
        capabilities=(option("save", persists_business_document=True),),
    ), "save").kind == NextStep.ASK
    assert validate_model_proposal(ctx(
        capabilities=(option(),),
        attempted_without_progress=("write:width",),
    ), "write:width").kind == NextStep.OBSERVE


def test_model_cannot_edit_without_required_source_fact():
    result = validate_model_proposal(ctx(
        capabilities=(option("hardware:select", documentation_key="compatible"),),
        pending_unknowns=("compatible",),
    ), "hardware:select")
    assert result.kind == NextStep.CONSULT
    fact = KnowledgeFact("compatible", "yes", SourceKind.LIVE_UI,
                         "catalogue-current-session", verified=True)
    assert validate_model_proposal(ctx(
        capabilities=(option("hardware:select", documentation_key="compatible"),),
        pending_unknowns=("compatible",), knowledge=(fact,),
    ), "hardware:select").kind == NextStep.ACT


def test_inspection_does_not_bypass_save_guard_or_repeat_guard():
    result = plan_next_step(ctx(
        pending_unknowns=("profile",),
        capabilities=(option("inspect:danger", persists_business_document=True),),
    ))
    assert result.kind == NextStep.CONSULT
    result = plan_next_step(ctx(
        pending_unknowns=("profile",),
        capabilities=(option("inspect:catalogue"),),
        attempted_without_progress=("inspect:catalogue",),
    ))
    assert result.kind == NextStep.CONSULT
