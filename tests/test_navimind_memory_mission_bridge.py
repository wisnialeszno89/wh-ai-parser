"""Codespaces acceptance: approved memory feeds whole virtual quotation missions."""
from dataclasses import replace

import pytest

from app.agent.learning.navimind_correction_rulebook import (
    Correction, LearningScope, RuleBook, RuleCase, propose_rule,
)
from app.agent.learning.navimind_memory_mission_bridge import (
    prepare_mission_with_memory, verify_memory_generation_unchanged,
)
from app.agent.learning.navimind_versioned_rule_memory import RuleMemoryStore
from app.agent.offers.windowhub_commercial_quote_routes import (
    QuoteCapabilities, QuoteRequest, TechnicalFinding, TechnicalStatus,
)
from app.agent.runtime.navimind_mission_coordinator import PositionTask
from app.agent.runtime.navimind_virtual_windowhub import VirtualWindowHub, run_virtual_mission


def env():
    return VirtualWindowHub("OFR/DEMO", QuoteCapabilities(
        exact_catalogue_construction_verified=False,
        description_field_verified=True, descriptive_position_supported=True,
        placeholder_position_supported=True, image_insert_supported=True,
        manual_price_field_verified=True,
        available_placeholder_width_mm=1000, available_placeholder_height_mm=1000,
    ))


def item(index="1", description="Oferta indywidualna"):
    return PositionTask(
        index,
        QuoteRequest(description, 1, requested_width_mm=2400, requested_height_mm=2750,
                     manual_unit_price="3500.00"),
        TechnicalFinding(TechnicalStatus.KNOWN_OUTSIDE_WARRANTY,
                         "Przekroczony wymiar", "manufacturer-evidence"),
    )


def saved_book(path, *, activate=True):
    store = RuleMemoryStore(path)
    book = RuleBook()
    scope = LearningScope("WindowHub", "commercial_quote", "description",
                          ("nonstandard",))
    correction = Correction("corr-a", "OFR/OTHER", "1", scope,
                            "Oferta indywidualna",
                            "Oferta indywidualna — wymaga sprawdzenia gwarancji.",
                            True, True)
    rule = propose_rule(correction, rule_id="warranty-wording")
    book.propose(rule)
    if activate:
        book.test(rule.rule_id, (
            RuleCase("positive-1", scope, correction.before, correction.after, True),
            RuleCase("positive-2", LearningScope(
                "WindowHub", "commercial_quote", "description",
                ("nonstandard", "extra")), correction.before, correction.after, True),
            RuleCase("negative", LearningScope(
                "WindowHub", "commercial_quote", "description",
                ("standard",)), correction.before, correction.before, True),
        ))
        book.approve(rule.rule_id, approver="seller", correction_id="corr-a")
    store.save(book, expected_generation=0)
    return store, book


def test_approved_rule_changes_description_and_virtual_mission_verifies_it(tmp_path):
    store, _ = saved_book(tmp_path / "rules.json")
    virtual = env()
    original = item()
    prepared = prepare_mission_with_memory(
        store, (original,), virtual.scene(),
        context_tags={"1": ("nonstandard",)},
    )
    assert prepared.memory_generation == 1
    assert len(prepared.applied) == 1
    assert prepared.applied[0].rule_id == "warranty-wording"
    assert original.request.description == "Oferta indywidualna"
    assert "sprawdzenia gwarancji" in prepared.tasks[0].request.description
    assert prepared.tasks[0].request.manual_unit_price == original.request.manual_unit_price
    assert prepared.tasks[0].request.requested_width_mm == original.request.requested_width_mm
    assert prepared.tasks[0].technical == original.technical
    assert not prepared.desktop_actions_performed
    assert not prepared.save_authorized
    trace = run_virtual_mission(prepared.tasks, virtual)
    assert trace.finished
    assert "sprawdzenia gwarancji" in virtual.positions["1"].description
    assert "poza zakresem gwarancji producenta" in virtual.positions["1"].description
    assert virtual.positions["1"].unit_price == "3500.00"
    assert not virtual.saved and not virtual.sent
    assert "outside_manufacturer_warranty" in str(trace.summary["positions"][0]["warnings"])


def test_rule_not_used_when_scope_tag_missing(tmp_path):
    store, _ = saved_book(tmp_path / "rules.json")
    virtual = env()
    prepared = prepare_mission_with_memory(store, (item(),), virtual.scene())
    assert prepared.applied == ()
    assert prepared.tasks[0].request.description == "Oferta indywidualna"


def test_unapproved_rule_not_used(tmp_path):
    store, _ = saved_book(tmp_path / "rules.json", activate=False)
    prepared = prepare_mission_with_memory(
        store, (item(),), env().scene(), context_tags={"1": ("nonstandard",)}
    )
    assert prepared.applied == ()


def test_exact_value_required_no_fuzzy_override(tmp_path):
    store, _ = saved_book(tmp_path / "rules.json")
    prepared = prepare_mission_with_memory(
        store, (item(description="Oferta niestandardowa"),), env().scene(),
        context_tags={"1": ("nonstandard",)},
    )
    assert prepared.applied == ()
    assert prepared.tasks[0].request.description == "Oferta niestandardowa"


def test_unverified_wrong_document_and_stale_scene_refuse_memory(tmp_path):
    store, _ = saved_book(tmp_path / "rules.json")
    virtual = env()
    for changed in (
        replace(virtual.scene(), document_identity_verified=False),
        replace(virtual.scene(), fresh=False),
        replace(virtual.scene(), application="Notepad"),
    ):
        with pytest.raises(ValueError, match="verified_exact_document_required"):
            prepare_mission_with_memory(store, (item(),), changed)


def test_revocation_changes_generation_and_stale_plan_cannot_be_dispatched(tmp_path):
    store, book = saved_book(tmp_path / "rules.json")
    plan = prepare_mission_with_memory(
        store, (item(),), env().scene(), context_tags={"1": ("nonstandard",)}
    )
    assert verify_memory_generation_unchanged(store, plan)
    book.revoke("warranty-wording", operator="seller")
    store.save(book, expected_generation=1)
    assert not verify_memory_generation_unchanged(store, plan)
    revised = prepare_mission_with_memory(
        store, (item(),), env().scene(), context_tags={"1": ("nonstandard",)}
    )
    assert revised.applied == ()


def test_different_position_scopes_do_not_cross_contaminate(tmp_path):
    store, _ = saved_book(tmp_path / "rules.json")
    tasks = (item("1"), item("2"))
    prepared = prepare_mission_with_memory(
        store, tasks, env().scene(), context_tags={"1": ("nonstandard",), "2": ()}
    )
    assert len(prepared.applied) == 1
    assert prepared.applied[0].position_id == "1"
    assert prepared.tasks[1].request.description == tasks[1].request.description


def test_duplicate_positions_and_unknown_scope_rejected(tmp_path):
    store, _ = saved_book(tmp_path / "rules.json")
    with pytest.raises(ValueError, match="nonempty_unique_positions_required"):
        prepare_mission_with_memory(store, (item("1"), item("1")), env().scene())
    with pytest.raises(ValueError, match="unknown_position_context"):
        prepare_mission_with_memory(store, (item(),), env().scene(),
                                    context_tags={"999": ("nonstandard",)})


def test_invalid_memory_fails_closed_before_any_mission_edit(tmp_path):
    store = RuleMemoryStore(tmp_path / "corrupt.json")
    store.path.write_text("{not-json", encoding="utf-8")
    virtual = env()
    with pytest.raises(ValueError, match="memory_unreadable"):
        prepare_mission_with_memory(store, (item(),), virtual.scene())
    assert virtual.positions == {}


def test_memorized_wording_is_not_a_catalogue_compatibility_fact(tmp_path):
    store, _ = saved_book(tmp_path / "rules.json")
    virtual = env()
    prepared = prepare_mission_with_memory(
        store, (item(),), virtual.scene(), context_tags={"1": ("nonstandard",)}
    )
    assert prepared.tasks[0].technical.status == TechnicalStatus.KNOWN_OUTSIDE_WARRANTY
    assert prepared.tasks[0].technical.reference == "manufacturer-evidence"
    assert virtual.capabilities.exact_catalogue_construction_verified is False
