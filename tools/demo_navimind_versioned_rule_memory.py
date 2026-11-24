"""Demonstrate approved NaviMind rules surviving a fresh Python store reload.

Creates only a temporary sandbox memory file, not a WindowHub document.
"""
from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.navimind_correction_rulebook import (
    Correction, LearningScope, RuleBook, RuleCase, propose_rule,
)
from app.agent.learning.navimind_memory_decision_bridge import consult_saved_rules
from app.agent.learning.navimind_versioned_rule_memory import RuleMemoryStore


def main() -> int:
    scope = LearningScope("WindowHub", "commercial_quote", "description", ("custom",))
    correction = Correction("demo-human-correction", "DEMO/1", "1", scope,
                            "Wycena indywidualna",
                            "Wycena indywidualna; sprawdzić warunki gwarancji.",
                            True, True)
    rule = propose_rule(correction, rule_id="demo-custom-description")
    book = RuleBook()
    book.propose(rule)
    book.test(rule.rule_id, (
        RuleCase("accepted-example-1", scope, correction.before, correction.after, True),
        RuleCase("accepted-example-2", LearningScope(
            "WindowHub", "commercial_quote", "description", ("custom", "colour")),
            correction.before, correction.after, True),
        RuleCase("not-for-word", LearningScope("Word", "commercial_quote",
                                             "description", ("custom",)),
                 correction.before, correction.before, True),
    ))
    book.approve(rule.rule_id, approver="demo_only",
                 correction_id=correction.correction_id)
    with TemporaryDirectory() as directory:
        file = Path(directory) / "memory-v1.json"
        store = RuleMemoryStore(file)
        generation = store.save(book, expected_generation=0)
        print(f"MEMORY_WRITTEN_GENERATION={generation}")
        reread = consult_saved_rules(RuleMemoryStore(file), scope, correction.before)
        print(f"RESTART_READ_GENERATION={reread.generation}")
        print(f"ACTIVE_SUGGESTION={reread.proposed_value}")
        print(f"DESKTOP_ACTION_PERFORMED={reread.applied_to_desktop}")
        book.revoke(rule.rule_id, operator="demo_only")
        next_generation = store.save(book, expected_generation=generation)
        after = consult_saved_rules(RuleMemoryStore(file), scope, correction.before)
        print(f"REVOCATION_GENERATION={next_generation}")
        print(f"AFTER_REVOCATION={after.proposed_value}")
        print("DEMO_MEMORY_FILE_AUTOMATICALLY_REMOVED=True")
    print("REAL_USER_APPROVAL=False")
    print("LIVE_WINDOWHUB_CONNECTED=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
