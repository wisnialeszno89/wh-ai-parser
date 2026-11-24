"""Execute a NON-PRODUCTION mock WindowHub quotation entirely in memory.

Codespaces / Linux compatible. This command neither connects to WindowHub,
nor loads production customer records, nor sends requests to NaviMind/Vercel.
"""
from __future__ import annotations

import json

from app.agent.offers.windowhub_commercial_quote_routes import (
    QuoteCapabilities, QuoteRequest, TechnicalFinding, TechnicalStatus,
)
from app.agent.runtime.navimind_mission_coordinator import PositionTask
from app.agent.runtime.navimind_virtual_windowhub import VirtualWindowHub, run_virtual_mission


def demo_tasks() -> tuple[PositionTask, ...]:
    return (
        PositionTask(
            "1",
            QuoteRequest(
                "Nietypowa konstrukcja z wizualizacją klienta",
                quantity=1, requested_width_mm=2300, requested_height_mm=2700,
                manual_unit_price="3400.00", image_reference="fixtures/window-example.png",
                image_use_authorized=True,
            ),
            TechnicalFinding(
                TechnicalStatus.KNOWN_OUTSIDE_WARRANTY,
                "Przykładowa konstrukcja poza deklarowanym zakresem gwarancyjnym",
                "demo_only_not_real_manufacturer_source",
            ),
        ),
        PositionTask(
            "2",
            QuoteRequest(
                "Pozycja opisowa dodatkowego elementu",
                quantity=1, requested_width_mm=600, requested_height_mm=500,
                manual_unit_price="620.00",
            ),
            TechnicalFinding(TechnicalStatus.NOT_CHECKED, "Weryfikacja przed produkcją"),
        ),
    )


def run() -> int:
    capabilities = QuoteCapabilities(
        exact_catalogue_construction_verified=False,
        description_field_verified=True,
        descriptive_position_supported=True,
        placeholder_position_supported=True,
        image_insert_supported=True,
        manual_price_field_verified=True,
        available_placeholder_width_mm=1000,
        available_placeholder_height_mm=1000,
    )
    env = VirtualWindowHub("OFR/DEMO", capabilities)
    trace = run_virtual_mission(demo_tasks(), env)
    print("VIRTUAL_WINDOWHUB_ONLY=True")
    print("REAL_APPLICATION_CONNECTED=False")
    print("SIMULATION_FINISHED=" + str(trace.finished))
    print("SIMULATION_STEPS=" + str(len(trace.actions)))
    for action in trace.actions:
        print("SIM_ACTION=" + action)
    print("SIM_REPORT=" + json.dumps(trace.summary, ensure_ascii=False, sort_keys=True))
    return 0 if trace.finished and not env.saved and not env.sent else 1


if __name__ == "__main__":
    raise SystemExit(run())
