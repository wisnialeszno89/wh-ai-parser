"""Opt-in price research workflow for NaviMind's pinned sales mission.

The search provider is an INJECTED, trusted integration, not an open URL
fetcher or an AI-generated tool call. No provider is configured by default;
thus the module makes no internet requests until a trusted host connects an
actual provider. It never edits, saves or prices WindowHub documents.

Only human-originating, CURRENT chat messages explicitly requesting a price
lookup can authorize research. A fresh message invalidates old model work.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Protocol
import re

from app.agent.offers.navimind_external_price_research import (
    PriceReference, PriceResearchRequest, PriceSuggestion,
    review_price_references,
)
from app.agent.runtime.navimind_mission_chat import (
    ChatMessage, MessageRole, MissionChat,
)


class ResearchStatus(str, Enum):
    SUGGESTIONS = "suggestions"
    NO_MATCH = "no_match"
    NOT_AVAILABLE = "not_available"
    REQUIRES_REVIEW = "requires_review"


@dataclass(frozen=True)
class PriceSearchQuery:
    category: str
    product_code: str | None
    width_mm: int | None
    height_mm: int | None
    requested_currency: str
    max_results: int = 8


@dataclass(frozen=True)
class ProviderObservation:
    """An already extracted, attributable public listing, NOT a quote."""
    source_kind: str
    source_url: str
    seller: str
    title: str
    observed_price: str
    currency: str
    comparable_category: str
    product_code: str | None = None
    width_mm: int | None = None
    height_mm: int | None = None
    includes_vat: bool | None = None
    shipping_included: bool | None = None
    installation_included: bool | None = None


class PriceSearchProvider(Protocol):
    def search(self, query: PriceSearchQuery) -> tuple[ProviderObservation, ...]:
        """Trusted integration implements public search and source extraction."""


@dataclass(frozen=True)
class ResearchReport:
    status: ResearchStatus
    document_key: str
    mission_revision: int
    originating_message_id: int
    results: tuple[PriceSuggestion, ...]
    reasons: tuple[str, ...]
    # Research never gives a license to alter prices or files.
    quoted_price_written: bool = False
    gui_actions_performed: bool = False
    internet_searched: bool = False


# Strict enough to exclude incidental references to price, including
# "don't search". This is not general-purpose language understanding:
# uncertain intent should remain unexecuted.
_PRICE_SEARCH = re.compile(
    r"\b(?:znajdź|znajdz|poszukaj|wyszukaj|sprawdź|sprawdz|"
    r"szukaj|porównaj|porownaj)\b.{0,100}"
    r"\b(?:cenę|cene|ceny|cen|wycenę|wycene|ofertę|oferte|oferty)\b",
    flags=re.IGNORECASE | re.DOTALL,
)
_NEGATION = re.compile(
    r"\b(?:nie|bez|zakaz|stop)\s+"
    r"(?:proszę\s+)?(?:szukaj|poszukaj|wyszukuj|wyszukaj|sprawdzaj|sprawdź|sprawdz)\b",
    flags=re.IGNORECASE,
)


def explicit_price_search_intent(message: str) -> bool:
    return (isinstance(message, str) and len(message) <= 4000
            and bool(_PRICE_SEARCH.search(message))
            and not bool(_NEGATION.search(message)))


def _human_chat_message(chat: MissionChat, message_id: int) -> tuple[ChatMessage, int]:
    snapshot = chat.snapshot()
    matching = [
        m for m in snapshot.messages
        if m.message_id == message_id and m.role == MessageRole.HUMAN
        and m.mission_revision == snapshot.mission_revision
    ]
    if len(matching) != 1:
        raise ValueError("price_search_requires_current_human_message")
    if not explicit_price_search_intent(matching[0].text):
        raise ValueError("price_search_not_explicitly_requested")
    return matching[0], snapshot.mission_revision


def _validated_reference(raw: ProviderObservation, today: date) -> PriceReference:
    from app.agent.offers.navimind_external_price_research import PriceSourceKind
    if not isinstance(raw, ProviderObservation):
        raise ValueError("untrusted_provider_listing")
    return PriceReference(
        source_kind=PriceSourceKind(raw.source_kind),
        source_url=raw.source_url,
        seller=raw.seller,
        title=raw.title,
        observed_price=raw.observed_price,
        currency=raw.currency,
        checked_on=today.isoformat(),
        comparable_category=raw.comparable_category,
        product_code=raw.product_code,
        width_mm=raw.width_mm,
        height_mm=raw.height_mm,
        includes_vat=raw.includes_vat,
        shipping_included=raw.shipping_included,
        installation_included=raw.installation_included,
    )


def search_price_for_current_chat(
    *,
    chat: MissionChat,
    human_message_id: int,
    request: PriceResearchRequest,
    provider: PriceSearchProvider | None,
    today: date,
) -> ResearchReport:
    """Bound and validate every source; results remain advisory-only.

    The provider can be a vetted commercial search API or a browser adapter.
    The host must independently verify page details before returning a
    ProviderObservation. A user-supplied external page is not executable
    instructions. Network is only reachable via the injected provider.
    """
    message, revision = _human_chat_message(chat, human_message_id)
    if request.requested_by_salesperson is not True:
        raise ValueError("price_search_requires_salesperson_opt_in")
    if not isinstance(today, date):
        raise ValueError("trusted_observation_date_required")
    if not isinstance(request.item_category, str) or not request.item_category.strip():
        raise ValueError("price_research_category_required")
    if provider is None:
        return ResearchReport(
            ResearchStatus.NOT_AVAILABLE, chat.document_key, revision,
            human_message_id, (), ("trusted_search_provider_not_connected",),
        )
    query = PriceSearchQuery(
        category=request.item_category.strip(),
        product_code=request.product_code,
        width_mm=request.width_mm,
        height_mm=request.height_mm,
        requested_currency=request.currency,
    )
    # Fail closed before invoking a real adapter if input cannot fit a
    # bounded query. Customer names, documents and arbitrary prompts are
    # deliberately never sent as search query fields.
    if len(query.category) > 80 or (query.product_code and len(query.product_code) > 80):
        raise ValueError("price_search_query_too_long")
    try:
        observations = provider.search(query)
    except Exception:
        return ResearchReport(
            ResearchStatus.NOT_AVAILABLE, chat.document_key, revision,
            human_message_id, (), ("trusted_search_provider_failed",),
            internet_searched=True,
        )
    # If the user changed the mission while an internet lookup was running,
    # never surface stale comparisons as though current.
    if chat.snapshot().mission_revision != revision:
        return ResearchReport(
            ResearchStatus.REQUIRES_REVIEW, chat.document_key, revision,
            human_message_id, (), ("mission_changed_during_price_search",),
            internet_searched=True,
        )
    if not isinstance(observations, (tuple, list)):
        return ResearchReport(
            ResearchStatus.REQUIRES_REVIEW, chat.document_key, revision,
            human_message_id, (), ("provider_results_malformed",),
            internet_searched=True,
        )
    parsed = []
    invalid = 0
    for raw in observations[:query.max_results]:
        try:
            parsed.append(_validated_reference(raw, today))
        except (TypeError, ValueError, AttributeError):
            invalid += 1
    suggestions = review_price_references(request, tuple(parsed))
    reasons = []
    if invalid:
        reasons.append("some_provider_results_rejected")
    if not suggestions:
        reasons.append("no_usable_verified_comparable_reference")
    return ResearchReport(
        ResearchStatus.SUGGESTIONS if suggestions else ResearchStatus.NO_MATCH,
        chat.document_key, revision, human_message_id,
        suggestions, tuple(reasons), internet_searched=True,
    )


def research_chat_summary(report: ResearchReport) -> str:
    """Safe user-facing description; NEVER promotes estimates to full prices."""
    if report.status == ResearchStatus.NOT_AVAILABLE:
        return "Nie mogę teraz sprawdzić cen online. Źródło wyszukiwania nie jest dostępne; pozycja pozostaje bez wyceny."
    if report.status == ResearchStatus.REQUIRES_REVIEW:
        return "W trakcie wyszukiwania zmieniło się zadanie lub dane były niepewne. Nie użyłem żadnej ceny."
    if report.status == ResearchStatus.NO_MATCH:
        return "Nie znalazłem wystarczająco porównywalnej oferty. Cena pozostaje nieustalona."
    return (
        f"Znalazłem {len(report.results)} orientacyjnych ofert porównawczych. "
        "Sprawdź kody produktów, wymiary, walutę, VAT i koszty dostawy/montażu. "
        "Nie wpisałem żadnej ceny do oferty."
    )
