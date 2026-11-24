"""Demo: 3-position virtual WindowHub quote, 2 parapets missing price.

NaviMind prepares dimensions/descriptions and the priced window, moves
forward rather than inventing 0, and reports gaps as unfinished.
No real WindowHub, file write, AI response or business approval.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.windowhub_commercial_quote_routes import (
    QuoteCapabilities, QuoteRequest, TechnicalFinding, TechnicalStatus,
)
from app.agent.runtime.navimind_mission_coordinator import PositionTask
from app.agent.runtime.navimind_virtual_windowhub import (
    VirtualWindowHub, run_virtual_mission,
)


def item(number, name, length, depth, price):
    return PositionTask(
        str(number),
        QuoteRequest(
            name, 1, requested_width_mm=length,
            requested_height_mm=depth, manual_unit_price=price,
        ),
        TechnicalFinding(TechnicalStatus.NOT_CHECKED,
                         "Szczegóły techniczne wymagają kontroli handlowca"),
        allow_unpriced_draft=(price is None),
    )


def main() -> int:
    env = VirtualWindowHub(
        "OFR/101",
        QuoteCapabilities(
            False, True, True, True, True, True, 1000, 1000,
        ),
    )
    tasks = (
        item(1, "Parapet zewnętrzny aluminiowy", 1900, 250, None),
        item(2, "Okno PCV dwuszybowe", 1400, 1200, "2800.00"),
        item(3, "Parapet zewnętrzny aluminiowy", 1000, 250, None),
    )
    trace = run_virtual_mission(tasks, env)
    report = trace.summary
    print("POSITIONS_PREPARED=" + str(report["draft_positions_prepared"]))
    print("UNPRICED_POSITION_IDS=" + ",".join(report["unpriced_position_ids"]))
    print("KNOWN_WINDOW_PRICE=" + str(env.positions["2"].unit_price))
    print("PARAPET_1_PRICE=" + str(env.positions["1"].unit_price))
    print("PARAPET_3_PRICE=" + str(env.positions["3"].unit_price))
    print("DRAFT_TERMINAL_REASON=" + trace.terminal_reason)
    print("FULLY_PRICED_QUOTATION=" + str(report["ready_for_final_customer_quote"]))
    print("PRICE_FABRICATED=False")
    print("AUTOSAVE=" + str(env.saved))
    print("AUTOSEND=" + str(env.sent))
    print("LIVE_WINDOWHUB_CONNECTED=False")
    return 0 if (
        report["draft_positions_prepared"] == 3
        and report["unpriced_position_ids"] == ["1", "3"]
        and env.positions["2"].unit_price == "2800.00"
        and env.positions["1"].unit_price is None
        and env.positions["3"].unit_price is None
        and not report["ready_for_final_customer_quote"]
        and not env.saved and not env.sent
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
