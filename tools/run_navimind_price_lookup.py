"""Operator-invoked market-price lookup for one non-catalogue product.

Network access is impossible without BOTH an explicit command flag and a
locally configured NAVIMIND_SERPAPI_KEY. Output is advisory-only; the CLI
never launches, saves or modifies WindowHub.

Example:
python tools/run_navimind_price_lookup.py --research-consent \
  --offer OFR/101 --category door_panel --code EK-02-A \
  --width 1100 --height 2200
"""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.navimind_external_price_research import PriceResearchRequest
from app.agent.runtime.navimind_serpapi_shopping_provider import (
    CATEGORY_TERMS, SerpApiShoppingProvider,
)
from app.agent.runtime.navimind_shared_control_host import NaviMindSharedHost
from app.agent.runtime.navimind_price_search_workflow import (
    compose_price_research_chat_reply, ResearchStatus,
)


def execute(*, offer: str, category: str, code: str | None,
            width: int | None, height: int | None, currency: str,
            research_consent: bool, provider=None, today=None) -> int:
    if not research_consent:
        print("RESEARCH_REFUSED=no_explicit_operator_consent")
        return 2
    if category not in CATEGORY_TERMS:
        print("RESEARCH_REFUSED=unsupported_category")
        return 2
    if not offer.strip() or not offer.upper().startswith("OFR/"):
        print("RESEARCH_REFUSED=invalid_offer_identifier")
        return 2
    host = NaviMindSharedHost(offer)
    message = host.chat.user_message(
        "Poszukaj ceny produktu: " + category
    )
    request = PriceResearchRequest(
        item_category=category,
        requested_by_salesperson=True,
        product_code=code,
        width_mm=width,
        height_mm=height,
        currency=currency,
    )
    active_provider = provider if provider is not None else SerpApiShoppingProvider.from_environment()
    report = host.research_price_for_chat(
        human_message_id=message.message_id,
        request=request,
        provider=active_provider,
        today=today if today is not None else date.today(),
    )
    print("RESEARCH_STATUS=" + report.status.value)
    print("RESEARCH_PROVIDER_INVOKED=" + str(report.provider_invoked))
    print("RESEARCH_RESULTS=" + str(len(report.results)))
    print("AUTOMATIC_PRICE_WRITE=" + str(report.quoted_price_written))
    print("WINDOWHUB_EXECUTED=False")
    print(compose_price_research_chat_reply(report))
    if report.status == ResearchStatus.NOT_AVAILABLE:
        return 3
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Explicitly consented, advisory-only public product price comparison"
    )
    parser.add_argument("--research-consent", action="store_true",
                        help="I authorize one online search for a product price reference")
    parser.add_argument("--offer", required=True, help="Pinned offer ID, e.g. OFR/101; never transmitted")
    parser.add_argument("--category", choices=sorted(CATEGORY_TERMS), required=True)
    parser.add_argument("--code", default=None, help="Product code, e.g. EK-02-A")
    parser.add_argument("--width", type=int, default=None, help="Item width in mm")
    parser.add_argument("--height", type=int, default=None, help="Item height in mm")
    parser.add_argument("--currency", choices=("PLN", "EUR"), default="PLN")
    args = parser.parse_args(argv)
    try:
        return execute(
            offer=args.offer, category=args.category, code=args.code,
            width=args.width, height=args.height,
            currency=args.currency,
            research_consent=args.research_consent,
        )
    except (ValueError, TypeError):
        # Do not echo arbitrary product input, confidential details or API key.
        print("RESEARCH_REFUSED=invalid_or_unverified_product_request")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
