"""Portable opt-in price-search workflow demo; fake results, no network.

This intentionally confirms the full chat opt-in and provenance flow without
claiming an online search provider or WindowHub integration is deployed.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.navimind_external_price_research import PriceResearchRequest
from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_price_search_workflow import (
    ProviderObservation, ResearchStatus,
    publish_research_to_chat, search_price_for_current_chat,
)


class SyntheticSearchProvider:
    def search(self, query):
        assert query.category == "door_panel"
        assert query.product_code == "EK-02-A"
        assert query.max_results == 8
        return (
            ProviderObservation(
                source_kind="marketplace",
                source_url="https://example.org/synthetic-listing-1",
                seller="Fikcyjny dostawca",
                title="Przykładowy panel drzwiowy EK-02-A",
                observed_price="870.00",
                currency="PLN",
                comparable_category="door_panel",
                product_code="EK-02-A",
                width_mm=1100,
                height_mm=2200,
            ),
        )


def main() -> int:
    chat = MissionChat(document_key="OFR/101", arbiter=LocalInputArbiter())
    m = chat.user_message("Poszukaj ceny panelu EK-02-A")
    request = PriceResearchRequest(
        item_category="door_panel",
        requested_by_salesperson=True,
        product_code="EK-02-A",
        width_mm=1100,
        height_mm=2200,
    )
    unavailable = search_price_for_current_chat(
        chat=chat, human_message_id=m.message_id,
        request=request, provider=None, today=date(2026, 11, 24),
    )
    synthetic = search_price_for_current_chat(
        chat=chat, human_message_id=m.message_id,
        request=request, provider=SyntheticSearchProvider(),
        today=date(2026, 11, 24),
    )
    published = publish_research_to_chat(chat, synthetic)
    print("RESEARCH_EXPLICITLY_REQUESTED=True")
    print("WITHOUT_PROVIDER=" + unavailable.status.value)
    print("WITH_SYNTHETIC_PROVIDER=" + synthetic.status.value)
    print("REFERENCE_COUNT=" + str(len(synthetic.results)))
    print("REFERENCE_PRICE=" + synthetic.results[0].reference.observed_price)
    print("REFERENCE_APPROVED=" + str(synthetic.results[0].approved_to_write))
    print("ADVISORY_CHAT_RESPONSE_PUBLISHED=" + str(published))
    print("AUTOMATIC_QUOTATION_PRICE_WRITE=" + str(synthetic.quoted_price_written))
    print("REAL_ONLINE_SEARCH_CONNECTED=False")
    print("WINDOWHUB_CONNECTED=False")
    return 0 if (
        unavailable.status == ResearchStatus.NOT_AVAILABLE
        and synthetic.status == ResearchStatus.SUGGESTIONS
        and published
        and not synthetic.quoted_price_written
        and not synthetic.results[0].approved_to_write
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
