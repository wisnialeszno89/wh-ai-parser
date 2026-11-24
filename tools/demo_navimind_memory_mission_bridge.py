"""Demo: approved memory -> mission plan -> in-memory WindowHub readback.

All customer/window information is synthetic. No real Windows program, browser,
production system, cloud API or actual user approval is involved.
"""
from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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


def run() -> int:
    with TemporaryDirectory() as folder:
        scope = LearningScope("WindowHub", "commercial_quote", "description",
                              ("nonstandard",))
        before = "Indywidualna wycena okna"
        after = "Indywidualna wycena okna. Warunki gwarancji do sprawdzenia."
        correction = Correction("demo-corr", "OFR/TEST-OLD", "1", scope,
                                before, after, True, True)
        rule = propose_rule(correction, rule_id="demo-learned-description")
        book = RuleBook()
        book.propose(rule)
        book.test(rule.rule_id, (
            RuleCase("positive-1", scope, before, after, True),
            RuleCase("positive-2", LearningScope(
                "WindowHub", "commercial_quote", "description",
                ("nonstandard", "special_color")), before, after, True),
            RuleCase("boundary", LearningScope(
                "WindowHub", "commercial_quote", "description",
                ("standard",)), before, before, True),
        ))
        # Demonstration approval, not a real salesperson's authorization.
        book.approve(rule.rule_id, approver="demo_only", correction_id="demo-corr")
        store = RuleMemoryStore(Path(folder) / "approved-rulebook.json")
        store.save(book, expected_generation=0)
        virtual = VirtualWindowHub("OFR/DEMO", QuoteCapabilities(
            False, True, True, True, True, True, 1000, 1000,
        ))
        tasks = (PositionTask(
            "1", QuoteRequest(before, 1, requested_width_mm=2250,
                              requested_height_mm=2750, manual_unit_price="3100.00"),
            TechnicalFinding(
                TechnicalStatus.KNOWN_OUTSIDE_WARRANTY,
                "Przykładowy przekroczony gabaryt",
                "demo-manufacturer-evidence",
            ),
        ),)
        prepared = prepare_mission_with_memory(
            store, tasks, virtual.scene(), context_tags={"1": ("nonstandard",)}
        )
        print("LEARNED_RULES_APPLIED=" + str(len(prepared.applied)))
        print("MEMORY_GENERATION=" + str(prepared.memory_generation))
        print("MEMORY_STILL_CURRENT=" + str(verify_memory_generation_unchanged(store, prepared)))
        trace = run_virtual_mission(prepared.tasks, virtual)
        print("SIMULATION_FINISHED=" + str(trace.finished))
        print("DESCRIPTION_HAS_LEARNED_WORDING=" + str(
            after in virtual.positions["1"].description
        ))
        print("DESCRIPTION_HAS_WARRANTY_WARNING=" + str(
            "poza zakresem gwarancji producenta" in virtual.positions["1"].description
        ))
        print("PRICE_UNCHANGED=" + str(virtual.positions["1"].unit_price == "3100.00"))
        print("SAVED=" + str(virtual.saved))
        print("SENT=" + str(virtual.sent))
        print("LIVE_WINDOWHUB_CONNECTED=False")
        print("REAL_OPERATOR_APPROVAL=False")
        return 0 if (
            trace.finished and len(prepared.applied) == 1
            and after in virtual.positions["1"].description
            and not virtual.saved and not virtual.sent
        ) else 1


if __name__ == "__main__":
    raise SystemExit(run())
