"""Safe, inspectable learning from human corrections (no OS or IO).

Correction is evidence for a candidate, not automatic permission. Promotion
requires a user's explicit approval and independently verified case tests.
Rule scope prevents accidental transfer between programs, controls or products.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RuleState(str, Enum):
    PROPOSED = "proposed"
    TESTED = "tested"
    ACTIVE = "active"
    REVOKED = "revoked"


@dataclass(frozen=True)
class LearningScope:
    application: str
    workflow: str
    field: str
    context_tags: tuple[str, ...] = ()

    def __post_init__(self):
        if not all((self.application.strip(), self.workflow.strip(), self.field.strip())):
            raise ValueError("scope_requires_application_workflow_field")
        if len(set(self.context_tags)) != len(self.context_tags):
            raise ValueError("duplicate_scope_tag")


@dataclass(frozen=True)
class Correction:
    """A fresh readback of a human-edited value, tied to one exact document."""
    correction_id: str
    document_id: str
    position_id: str
    scope: LearningScope
    before: str
    after: str
    user_confirmed_intent: bool
    independently_observed: bool

    def __post_init__(self):
        if not self.correction_id or not self.document_id or not self.position_id:
            raise ValueError("correction_identity_required")
        if not self.after.strip() or self.after == self.before:
            raise ValueError("changed_value_required")


@dataclass(frozen=True)
class RuleCandidate:
    """Literal mapping; not prompt text, Python code or an executable action."""
    rule_id: str
    scope: LearningScope
    match_value: str
    replacement_value: str
    correction_id: str

    def __post_init__(self):
        if not self.rule_id.strip() or self.match_value == self.replacement_value:
            raise ValueError("invalid_rule_candidate")


@dataclass(frozen=True)
class RuleCase:
    """A human-selected case with independently established expected result."""
    case_id: str
    scope: LearningScope
    input_value: str
    expected_value: str
    independently_verified: bool

    def __post_init__(self):
        if not self.case_id:
            raise ValueError("test_case_id_required")


@dataclass(frozen=True)
class RuleTestReport:
    rule_id: str
    passed: int
    failed: int
    unverified: int
    positive_passed: int
    boundary_passed: int
    cases: tuple[str, ...]

    @property
    def eligible_for_promotion(self) -> bool:
        return (self.positive_passed >= 2 and self.boundary_passed >= 1
                and self.failed == 0 and self.unverified == 0)


@dataclass
class RuleRecord:
    candidate: RuleCandidate
    state: RuleState = RuleState.PROPOSED
    tested_report: RuleTestReport | None = None
    approved_by: str | None = None
    history: list[str] = field(default_factory=list)


def propose_rule(correction: Correction, *, rule_id: str) -> RuleCandidate:
    """Only intentional, independently observed corrections create proposals."""
    if not correction.user_confirmed_intent or not correction.independently_observed:
        raise ValueError("confirmed_observed_correction_required")
    return RuleCandidate(
        rule_id=rule_id, scope=correction.scope, match_value=correction.before,
        replacement_value=correction.after, correction_id=correction.correction_id,
    )


def scope_matches(rule_scope: LearningScope, actual: LearningScope) -> bool:
    """Same app/workflow/field; actual context must cover all rule conditions."""
    return (
        rule_scope.application == actual.application
        and rule_scope.workflow == actual.workflow
        and rule_scope.field == actual.field
        and set(rule_scope.context_tags).issubset(actual.context_tags)
    )


def evaluate_rule(candidate: RuleCandidate,
                  cases: tuple[RuleCase, ...]) -> RuleTestReport:
    """Conservative exact mapping, evaluated against independent expectations.

    At least two *different* verified case ids are needed for promotion.
    Unverified cases cannot accidentally count as correct. Include negative
    cases that should remain unchanged to test the scope boundary.
    """
    if len({item.case_id for item in cases}) != len(cases):
        raise ValueError("duplicate_test_cases")
    passed = failed = unverified = positive_passed = boundary_passed = 0
    for case in cases:
        if not case.independently_verified:
            unverified += 1
            continue
        actual = (
            candidate.replacement_value
            if scope_matches(candidate.scope, case.scope)
            and case.input_value == candidate.match_value
            else case.input_value
        )
        if actual == case.expected_value:
            passed += 1
            eligible_context = (
                scope_matches(candidate.scope, case.scope)
                and case.input_value == candidate.match_value
            )
            if eligible_context:
                positive_passed += 1
            else:
                boundary_passed += 1
        else:
            failed += 1
    return RuleTestReport(
        candidate.rule_id, passed, failed, unverified,
        positive_passed, boundary_passed, tuple(item.case_id for item in cases),
    )


class RuleBook:
    """In-memory registry. File storage and model integration require review."""
    def __init__(self):
        self.records: dict[str, RuleRecord] = {}

    def propose(self, candidate: RuleCandidate) -> RuleRecord:
        if candidate.rule_id in self.records:
            raise ValueError("rule_id_already_exists")
        record = RuleRecord(candidate=candidate, history=["proposed"])
        self.records[candidate.rule_id] = record
        return record

    def test(self, rule_id: str, cases: tuple[RuleCase, ...]) -> RuleTestReport:
        record = self.records[rule_id]
        if record.state in (RuleState.ACTIVE, RuleState.REVOKED):
            raise ValueError("rule_not_testable_in_current_state")
        report = evaluate_rule(record.candidate, cases)
        record.tested_report = report
        record.state = RuleState.TESTED if report.eligible_for_promotion else RuleState.PROPOSED
        record.history.append("tested:" + str(report.passed) + "/" + str(len(cases)))
        return report

    def approve(self, rule_id: str, *, approver: str,
                correction_id: str) -> RuleRecord:
        record = self.records[rule_id]
        if not approver.strip() or record.candidate.correction_id != correction_id:
            raise ValueError("explicit_matching_approval_required")
        if (record.state != RuleState.TESTED or record.tested_report is None
                or not record.tested_report.eligible_for_promotion):
            raise ValueError("verified_tests_required_before_activation")
        for other in self.records.values():
            if other is record or other.state != RuleState.ACTIVE:
                continue
            if (other.candidate.scope == record.candidate.scope
                    and other.candidate.match_value == record.candidate.match_value):
                raise ValueError("conflicting_active_rule")
        record.state = RuleState.ACTIVE
        record.approved_by = approver
        record.history.append("approved:" + approver)
        return record

    def revoke(self, rule_id: str, *, operator: str) -> None:
        if not operator.strip():
            raise ValueError("operator_required")
        record = self.records[rule_id]
        if record.state != RuleState.ACTIVE:
            raise ValueError("only_active_rules_can_be_revoked")
        record.state = RuleState.REVOKED
        record.history.append("revoked:" + operator)

    def suggest(self, scope: LearningScope, value: str) -> tuple[str, str] | None:
        """Suggested textual value, never direct GUI action or autosave."""
        matches = [
            r.candidate for r in self.records.values()
            if r.state == RuleState.ACTIVE
            and scope_matches(r.candidate.scope, scope)
            and r.candidate.match_value == value
        ]
        if len(matches) != 1:
            return None
        return matches[0].rule_id, matches[0].replacement_value
