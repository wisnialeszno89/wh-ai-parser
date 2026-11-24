"""Portable demonstration: out-of-catalogue Veyna-style panel and garage door.

All prices, names and sample image references below are synthetic mission
inputs, NOT verified vendor catalogue facts or real downloadable imagery.
No live WindowHub control and no market search are performed.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.navimind_external_catalogue_items import (
    ExternalComponent, ExternalItemKind, ExternalItemSpec,
    ReferenceImage, build_external_draft,
)
from app.agent.offers.navimind_external_price_research import (
    PriceReference, PriceResearchRequest, PriceSourceKind,
    review_price_references,
)
from app.agent.offers.windowhub_commercial_quote_routes import QuoteCapabilities
from app.agent.runtime.navimind_virtual_windowhub import VirtualWindowHub, run_virtual_mission


def main() -> int:
    door = build_external_draft(ExternalItemSpec(
        position_id="1",
        kind=ExternalItemKind.DOOR_WITH_EXTERNAL_PANEL,
        product_description="Drzwi wejściowe z panelem firmy zewnętrznej",
        width_mm=1100, height_mm=2200,
        supplier="Veyna", supplier_model="EK-02-A",
        components=(
            ExternalComponent("rama i skrzydło", "przykładowa wycena handlowca", "2650.00"),
            ExternalComponent("panel zewnętrzny EK-02-A", "cena dostawcy nieustalona"),
        ),
        illustration=ReferenceImage(
            "demo/example-panel.png", "Przykładowe zdjęcie panela",
            "fikcyjne dane do symulacji", True, True,
        ),
    ))
    garage = build_external_draft(ExternalItemSpec(
        position_id="2", kind=ExternalItemKind.GARAGE_DOOR,
        product_description="Brama segmentowa spoza katalogu",
        width_mm=3000, height_mm=2300,
    ))
    env = VirtualWindowHub("OFR/101", QuoteCapabilities(
        False, True, True, True, True, True, 1000, 1000,
    ))
    result = run_virtual_mission((door.task, garage.task), env)
    report = result.summary
    print("EXTERNAL_POSITIONS_PREPARED=" + str(report["draft_positions_prepared"]))
    print("UNPRICED_POSITION_IDS=" + ",".join(report["unpriced_position_ids"]))
    print("PANEL_CODE_PRESENT=" + str("EK-02-A" in env.positions["1"].description))
    print("DOOR_IMAGE_EXAMPLE_PRESENT=" + str(
        env.positions["1"].image_reference == "demo/example-panel.png"
    ))
    print("DOOR_TOTAL_PRICE=" + str(env.positions["1"].unit_price))
    print("GARAGE_TOTAL_PRICE=" + str(env.positions["2"].unit_price))
    print("FULLY_PRICED=" + str(report["ready_for_final_customer_quote"]))

    # A fake listing tests only advisory review (NOT an actual Internet search).
    listing = PriceReference(
        source_kind=PriceSourceKind.MARKETPLACE,
        source_url="https://example.org/synthetic-market-listing",
        seller="Fikcyjny sprzedawca", title="Przykładowa oferta panelu",
        observed_price="890.00", currency="PLN", checked_on="2026-11-24",
        comparable_category="door_panel", product_code="EK-02-A",
        width_mm=1100, height_mm=2200,
    )
    before = review_price_references(
        PriceResearchRequest("door_panel", False, "EK-02-A", 1100, 2200),
        (listing,),
    )
    after = review_price_references(
        PriceResearchRequest("door_panel", True, "EK-02-A", 1100, 2200),
        (listing,),
    )
    print("REFERENCE_UNREQUESTED=" + str(len(before)))
    print("REFERENCE_REQUESTED=" + str(len(after)))
    print("REFERENCE_AUTO_APPROVED=" + str(
        any(x.approved_to_write for x in after)
    ))
    print("SIMULATED_LISTING_ONLY=True")
    print("ONLINE_SEARCH_PERFORMED=False")
    print("REAL_WINDOWHUB_CONNECTED=False")
    print("SAVED=" + str(env.saved))
    print("SENT=" + str(env.sent))
    return 0 if (
        report["draft_positions_prepared"] == 2
        and report["unpriced_position_ids"] == ["1", "2"]
        and env.positions["1"].unit_price is None
        and env.positions["2"].unit_price is None
        and env.positions["1"].image_reference == "demo/example-panel.png"
        and not before and len(after) == 1
        and not after[0].approved_to_write
        and not env.saved and not env.sent
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
