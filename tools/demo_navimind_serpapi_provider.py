"""Synthetic end-to-end demo of the *real provider adapter* with fake HTTP.

This tests the exact data shape and host/chat path of the SerpApi adapter,
without making any network request or spending an API credit.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.navimind_external_price_research import PriceResearchRequest
from app.agent.runtime.navimind_serpapi_shopping_provider import SerpApiShoppingProvider
from app.agent.runtime.navimind_shared_control_host import NaviMindSharedHost


def synthetic_http(url: str, *, timeout: float):
    assert url.startswith("https://serpapi.com/search.json?")
    assert timeout <= 25.0
    return {
        "shopping_results": [
            {
                "title": "Panel drzwiowy EK-02-A 1100x2200",
                "source": "Demo sklep",
                "price": "870,00 zł",
                "extracted_price": 870.0,
                "product_link": "https://www.google.com/shopping/product/123",
            },
            {
                "title": "Drzwi kompletne z innym panelem",
                "source": "Demo sklep 2",
                "price": "3200,00 zł",
                "extracted_price": 3200.0,
                "product_link": "https://www.google.com/shopping/product/456",
            },
        ],
    }


def main() -> int:
    host = NaviMindSharedHost("OFR/101")
    human = host.chat.user_message("Poszukaj ceny panelu EK-02-A")
    provider = SerpApiShoppingProvider(
        "synthetic-only-key", transport=synthetic_http,
    )
    report = host.research_price_for_chat(
        human_message_id=human.message_id,
        request=PriceResearchRequest(
            item_category="door_panel",
            requested_by_salesperson=True,
            product_code="EK-02-A",
            width_mm=1100, height_mm=2200,
        ),
        provider=provider,
        today=date(2026, 11, 24),
    )
    print("HTTP_TRANSPORT_SYNTHETIC=True")
    print("SOURCE_RECORD_COUNT=" + str(len(report.results)))
    print("VERIFIED_FIRST_CODE=" + str(report.results[0].reference.product_code))
    print("UNVERIFIED_SECOND_CODE=" + str(report.results[1].reference.product_code))
    print("CHAT_ADVISORY_PUBLISHED=" + str(
        host.chat.snapshot().messages[-1].role.value == "agent"
    ))
    print("HUMAN_CONTROL=" + str(host.controller.snapshot().human_controls))
    print("AUTOMATIC_PRICE_WRITE=" + str(report.quoted_price_written))
    print("REAL_NETWORK_REQUESTS=0")
    print("REAL_WINDOWHUB_CONNECTED=False")
    return 0 if (
        len(report.results) == 2
        and report.results[0].reference.product_code == "EK-02-A"
        and report.results[1].reference.product_code is None
        and host.controller.snapshot().human_controls
        and not report.quoted_price_written
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
