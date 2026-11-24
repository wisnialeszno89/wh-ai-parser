"""Memory->decision bridge is scoped, read-only and fails closed."""
from app.agent.learning.navimind_correction_rulebook import (
    Correction, LearningScope, RuleBook, RuleCase, propose_rule,
)
from app.agent.learning.navimind_versioned_rule_memory import RuleMemoryStore
from app.agent.learning.navimind_memory_decision_bridge import consult_saved_rules
from app.agent.reasoning.navimind_evidence_decision_engine import SourceKind


def build_saved_rule(path):
    scope = LearningScope("WindowHub", "commercial_quote", "description", ("special",))
    change = Correction("correction-001", "OFR/1", "1", scope, "Base", "Reviewed", True, True)
    candidate = propose_rule(change, rule_id="reviewed-description")
    book = RuleBook()
    book.propose(candidate)
    book.test(candidate.rule_id, (
        RuleCase("positive-1", scope, "Base", "Reviewed", True),
        RuleCase("positive-2", LearningScope("WindowHub", "commercial_quote", "description",
                                          ("special", "additional")), "Base", "Reviewed", True),
        RuleCase("boundary", LearningScope("Word", "commercial_quote", "description",
                                         ("special",)), "Base", "Base", True),
    ))
    book.approve(candidate.rule_id, approver="tester", correction_id="correction-001")
    store = RuleMemoryStore(path)
    store.save(book, expected_generation=0)
    return store, book, scope


def test_saved_rule_becomes_read_only_evidence(tmp_path):
    store, _, scope = build_saved_rule(tmp_path / "rules.json")
    consulted = consult_saved_rules(store, scope, "Base")
    assert consulted.generation == 1
    assert consulted.matched_rule_id == "reviewed-description"
    assert consulted.proposed_value == "Reviewed"
    assert len(consulted.knowledge) == 1
    assert consulted.knowledge[0].source == SourceKind.LOCAL_RULE
    assert consulted.knowledge[0].verified
    assert not consulted.applied_to_desktop
    assert not consulted.production_approved


def test_not_applied_to_other_application_or_field(tmp_path):
    store, _, scope = build_saved_rule(tmp_path / "rules.json")
    other_app = LearningScope("Excel", "commercial_quote", "description", ("special",))
    other_field = LearningScope("WindowHub", "commercial_quote", "price", ("special",))
    assert consult_saved_rules(store, other_app, "Base").knowledge == ()
    assert consult_saved_rules(store, other_field, "Base").knowledge == ()
    assert consult_saved_rules(store, scope, "Another value").knowledge == ()


def test_revoke_disables_bridge_after_restart(tmp_path):
    store, book, scope = build_saved_rule(tmp_path / "rules.json")
    book.revoke("reviewed-description", operator="tester")
    store.save(book, expected_generation=1)
    consulted = consult_saved_rules(RuleMemoryStore(store.path), scope, "Base")
    assert consulted.generation == 2
    assert consulted.knowledge == ()
    assert consulted.matched_rule_id is None


def test_empty_memory_is_not_a_claim_of_technical_compatibility(tmp_path):
    consulted = consult_saved_rules(
        RuleMemoryStore(tmp_path / "nonexistent.json"),
        LearningScope("WindowHub", "commercial_quote", "description", ("special",)),
        "Base",
    )
    assert consulted.knowledge == ()
    assert consulted.generation == 0
