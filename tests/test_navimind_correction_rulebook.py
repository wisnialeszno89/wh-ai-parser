"""Portable training tests: corrective examples, boundary cases, revocation."""
import pytest

from app.agent.learning.navimind_correction_rulebook import (
    Correction, LearningScope, RuleBook, RuleCase, RuleState,
    evaluate_rule, propose_rule,
)


def scope(*tags):
    return LearningScope("WindowHub", "commercial_quote", "description", tags)


def corrected(**changes):
    kwargs = dict(
        correction_id="correction-1", document_id="OFR/101", position_id="2",
        scope=scope("out_of_warranty"),
        before="Wycena indywidualna",
        after="Wycena indywidualna. Wymaga weryfikacji gwarancji.",
        user_confirmed_intent=True, independently_observed=True,
    )
    kwargs.update(changes)
    return Correction(**kwargs)


def cases():
    return (
        RuleCase("same-context", scope("out_of_warranty"),
                 "Wycena indywidualna",
                 "Wycena indywidualna. Wymaga weryfikacji gwarancji.", True),
        RuleCase("compatible-tags", scope("out_of_warranty", "anthracite"),
                 "Wycena indywidualna",
                 "Wycena indywidualna. Wymaga weryfikacji gwarancji.", True),
        RuleCase("other-context", scope("normal"),
                 "Wycena indywidualna", "Wycena indywidualna", True),
        RuleCase("different-program",
                 LearningScope("Notepad", "commercial_quote", "description",
                               ("out_of_warranty",)),
                 "Wycena indywidualna", "Wycena indywidualna", True),
        RuleCase("different-field",
                 LearningScope("WindowHub", "commercial_quote", "price",
                               ("out_of_warranty",)),
                 "Wycena indywidualna", "Wycena indywidualna", True),
    )


def test_single_observed_correction_is_proposal_not_active_knowledge():
    rule = propose_rule(corrected(), rule_id="warning-1")
    book = RuleBook()
    assert book.propose(rule).state == RuleState.PROPOSED
    assert book.suggest(scope("out_of_warranty"), rule.match_value) is None


def test_unconfirmed_or_unobserved_correction_does_not_train():
    for changes in ({"independently_observed": False},
                    {"user_confirmed_intent": False}):
        with pytest.raises(ValueError, match="confirmed_observed"):
            propose_rule(corrected(**changes), rule_id="bad")


def test_rule_can_only_activate_after_verified_tests_and_approval():
    rule = propose_rule(corrected(), rule_id="warning-1")
    book = RuleBook()
    book.propose(rule)
    with pytest.raises(ValueError, match="verified_tests_required"):
        book.approve(rule.rule_id, approver="operator", correction_id="correction-1")
    report = book.test(rule.rule_id, cases())
    assert report.passed == 5
    assert report.eligible_for_promotion
    assert book.suggest(scope("out_of_warranty"), rule.match_value) is None
    record = book.approve(rule.rule_id, approver="operator", correction_id="correction-1")
    assert record.state == RuleState.ACTIVE
    assert book.suggest(scope("out_of_warranty", "extra"), rule.match_value) == (
        rule.rule_id, rule.replacement_value,
    )


def test_rule_never_changes_different_program_or_other_context():
    rule = propose_rule(corrected(), rule_id="warning-1")
    book = RuleBook()
    book.propose(rule)
    book.test(rule.rule_id, cases())
    book.approve(rule.rule_id, approver="seller", correction_id="correction-1")
    assert book.suggest(scope("other_context"), rule.match_value) is None
    assert book.suggest(
        LearningScope("Excel", "commercial_quote", "description", ("out_of_warranty",)),
        rule.match_value,
    ) is None
    assert book.suggest(scope("out_of_warranty"), "Different text") is None


def test_failed_regression_case_blocks_rule_activation():
    rule = propose_rule(corrected(), rule_id="warning-1")
    book = RuleBook()
    book.propose(rule)
    bad = cases() + (
        RuleCase("conflicting-expectation", scope("out_of_warranty"),
                 rule.match_value, "Keep original", True),
    )
    report = book.test(rule.rule_id, bad)
    assert report.failed == 1
    assert not report.eligible_for_promotion
    with pytest.raises(ValueError, match="verified_tests_required"):
        book.approve(rule.rule_id, approver="seller", correction_id="correction-1")


def test_unverified_case_is_not_treated_as_passed():
    rule = propose_rule(corrected(), rule_id="warning-1")
    report = evaluate_rule(rule, (
        RuleCase("a", scope("out_of_warranty"), rule.match_value,
                 rule.replacement_value, True),
        RuleCase("b", scope("out_of_warranty", "test"), rule.match_value,
                 rule.replacement_value, False),
    ))
    assert report.passed == 1
    assert report.unverified == 1
    assert not report.eligible_for_promotion


def test_one_example_cannot_promote_general_rule():
    rule = propose_rule(corrected(), rule_id="warning-1")
    book = RuleBook()
    book.propose(rule)
    report = book.test(rule.rule_id, cases()[:1])
    assert not report.eligible_for_promotion


def test_duplicate_case_ids_cannot_inflate_promotion_evidence():
    rule = propose_rule(corrected(), rule_id="warning-1")
    with pytest.raises(ValueError, match="duplicate_test_cases"):
        evaluate_rule(rule, cases()[:1] + cases()[:1])


def test_approval_must_identify_same_correction_and_real_operator():
    rule = propose_rule(corrected(), rule_id="warning-1")
    book = RuleBook()
    book.propose(rule)
    book.test(rule.rule_id, cases())
    with pytest.raises(ValueError, match="explicit_matching_approval"):
        book.approve(rule.rule_id, approver="operator", correction_id="different")
    with pytest.raises(ValueError, match="explicit_matching_approval"):
        book.approve(rule.rule_id, approver="", correction_id="correction-1")


def test_revoked_rule_stops_matching_immediately():
    rule = propose_rule(corrected(), rule_id="warning-1")
    book = RuleBook()
    book.propose(rule)
    book.test(rule.rule_id, cases())
    book.approve(rule.rule_id, approver="seller", correction_id="correction-1")
    book.revoke(rule.rule_id, operator="seller")
    assert book.records[rule.rule_id].state == RuleState.REVOKED
    assert book.suggest(scope("out_of_warranty"), rule.match_value) is None
    with pytest.raises(ValueError, match="rule_not_testable"):
        book.test(rule.rule_id, cases())


def test_second_conflicting_active_rule_cannot_be_enabled():
    one = propose_rule(corrected(), rule_id="one")
    two = propose_rule(corrected(correction_id="correction-2",
                                 after="Nowy sprzeczny opis"), rule_id="two")
    book = RuleBook()
    book.propose(one)
    book.test(one.rule_id, cases())
    book.approve(one.rule_id, approver="seller", correction_id="correction-1")
    book.propose(two)
    two_cases = (
        RuleCase("one", scope("out_of_warranty"), two.match_value,
                 two.replacement_value, True),
        RuleCase("two", scope("out_of_warranty", "extra"), two.match_value,
                 two.replacement_value, True),
        RuleCase("outside", scope("normal"), two.match_value,
                 two.match_value, True),
    )
    book.test(two.rule_id, two_cases)
    with pytest.raises(ValueError, match="conflicting_active_rule"):
        book.approve(two.rule_id, approver="seller", correction_id="correction-2")


def test_proposal_is_never_direct_gui_action_or_permission_to_save():
    rule = propose_rule(corrected(), rule_id="warning-1")
    book = RuleBook()
    book.propose(rule)
    book.test(rule.rule_id, cases())
    book.approve(rule.rule_id, approver="seller", correction_id="correction-1")
    suggestion = book.suggest(scope("out_of_warranty"), rule.match_value)
    assert isinstance(suggestion, tuple)
    assert len(suggestion) == 2
    assert not hasattr(book, "execute_windows")
    assert not hasattr(book, "save_offer")


def test_positive_only_passes_cannot_promote_without_scope_boundary():
    rule = propose_rule(corrected(), rule_id="warning-1")
    book = RuleBook()
    book.propose(rule)
    report = book.test(rule.rule_id, cases()[:2])
    assert report.passed == 2
    assert report.positive_passed == 2
    assert report.boundary_passed == 0
    assert not report.eligible_for_promotion


def test_negative_only_passes_cannot_promote_without_positive_examples():
    rule = propose_rule(corrected(), rule_id="warning-1")
    book = RuleBook()
    book.propose(rule)
    report = book.test(rule.rule_id, cases()[2:])
    assert report.passed == 3
    assert report.positive_passed == 0
    assert report.boundary_passed == 3
    assert not report.eligible_for_promotion
