"""Demonstrate safe correction learning entirely offline in Codespaces."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.navimind_correction_rulebook import (
    Correction, LearningScope, RuleBook, RuleCase, propose_rule,
)


def main() -> int:
    scope = LearningScope("WindowHub", "commercial_quote", "description",
                          ("out_of_warranty",))
    original = "Wycena indywidualna"
    improved = "Wycena indywidualna. Uwaga: wymaga przeglądu gwarancji."
    change = Correction(
        "demo-correction-1", "OFR/DEMO", "1", scope,
        original, improved, True, True,
    )
    book = RuleBook()
    candidate = propose_rule(change, rule_id="demo-warranty-description")
    book.propose(candidate)
    print("PROPOSED_STATE=" + book.records[candidate.rule_id].state.value)
    print("BEFORE_APPROVAL=" + str(book.suggest(scope, original)))
    cases = (
        RuleCase("same", scope, original, improved, True),
        RuleCase("compatible", LearningScope("WindowHub", "commercial_quote",
                 "description", ("out_of_warranty", "anthracite")),
                 original, improved, True),
        RuleCase("different-scope", LearningScope("WindowHub", "commercial_quote",
                 "description", ("standard",)), original, original, True),
    )
    report = book.test(candidate.rule_id, cases)
    print(f"TESTS={report.passed} passed, {report.failed} failed, {report.unverified} unverified")
    print("ELIGIBLE=" + str(report.eligible_for_promotion))
    # DEMONSTRATION APPROVAL: no real operator consent is inferred from this.
    book.approve(candidate.rule_id, approver="demo_only", correction_id=change.correction_id)
    print("ACTIVE_SUGGESTION=" + str(book.suggest(scope, original)))
    print("OTHER_SCOPE_SUGGESTION=" + str(book.suggest(cases[-1].scope, original)))
    book.revoke(candidate.rule_id, operator="demo_only")
    print("AFTER_REVOCATION=" + str(book.suggest(scope, original)))
    print("REAL_USER_APPROVAL=False")
    print("LIVE_WINDOWHUB_CONNECTED=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
