"""User-requested live price research uses only injected trusted providers."""
from __future__ import annotations

from datetime import date

import pytest

from app.agent.offers.navimind_external_price_research import PriceResearchRequest
from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_price_search_workflow import (
    ProviderObservation, ResearchStatus, explicit_price_search_intent,
    research_chat_summary, search_price_for_current_chat,
    compose_price_research_chat_reply, publish_research_to_chat,
)

DATE = date(2026, 11, 24)


class FakeProvider:
    def __init__(self, results=()):
        self.calls = []
        self.results = results
        self.on_search = None

    def search(self, query):
        self.calls.append(query)
        if self.on_search:
            self.on_search()
        return self.results


def listing(**changes):
    values = dict(
        source_kind="marketplace",
        source_url="https://www.example.org/items/123",
        seller="Fikcyjny sprzedawca",
        title="Panel drzwiowy dekoracyjny, model demonstracyjny",
        observed_price="840.00",
        currency="PLN",
        comparable_category="door_panel",
        product_code="EK-02-A",
        width_mm=1100,
        height_mm=2200,
    )
    values.update(changes)
    return ProviderObservation(**values)


def setup(message="Poszukaj ceny panelu EK-02-A"):
    chat = MissionChat(document_key="OFR/101", arbiter=LocalInputArbiter())
    msg = chat.user_message(message)
    request = PriceResearchRequest(
        item_category="door_panel",
        requested_by_salesperson=True,
        product_code="EK-02-A",
        width_mm=1100, height_mm=2200,
    )
    return chat, msg, request


def run(chat, msg, request, provider):
    return search_price_for_current_chat(
        chat=chat, human_message_id=msg.message_id,
        request=request, provider=provider, today=DATE,
    )


@pytest.mark.parametrize("message", [
    "Znajdź cenę panelu EK-02-A",
    "Poszukaj ceny bramy garażowej",
    "Sprawdź cenę podobnego produktu",
    "Wyszukaj oferty na panel",
    "Porównaj ceny u dostawców",
])
def test_explicit_polish_price_instructions_are_allowed(message):
    assert explicit_price_search_intent(message)


@pytest.mark.parametrize("message", [
    "Dodaj panel EK-02-A, cena nieznana",
    "Nie szukaj ceny panelu",
    "Bez szukaj ceny, proszę",
    "Cena z oferty jest prawidłowa",
    "Szukaj producenta, nie szukaj ceny",
])
def test_ordinary_or_negative_price_mentions_do_not_trigger_search(message):
    assert not explicit_price_search_intent(message)


def test_provider_is_never_called_without_explicit_current_human_request():
    chat, msg, req = setup("Dodaj panel EK-02-A bez ceny")
    provider = FakeProvider((listing(),))
    with pytest.raises(ValueError, match="not_explicitly_requested"):
        run(chat, msg, req, provider)
    assert provider.calls == []


def test_opt_in_flag_is_necessary_in_addition_to_chat_instruction():
    chat, msg, req = setup()
    provider = FakeProvider((listing(),))
    with pytest.raises(ValueError, match="requires_salesperson_opt_in"):
        run(chat, msg, PriceResearchRequest("door_panel", False), provider)
    assert not provider.calls


def test_no_provider_means_no_internet_or_fake_price():
    chat, msg, req = setup()
    report = run(chat, msg, req, None)
    assert report.status == ResearchStatus.NOT_AVAILABLE
    assert report.results == ()
    assert not report.provider_invoked
    assert not report.quoted_price_written
    assert "nie jest dostępne" in research_chat_summary(report)


def test_exact_match_is_still_only_merchant_reference_not_quote():
    chat, msg, req = setup()
    provider = FakeProvider((listing(),))
    report = run(chat, msg, req, provider)
    assert report.status == ResearchStatus.SUGGESTIONS
    assert len(provider.calls) == 1
    assert provider.calls[0].max_results == 8
    assert report.document_key == "OFR/101"
    assert report.mission_revision == 1
    assert report.results[0].comparison == "matching_code_and_dimensions_unverified_other_terms"
    assert not report.results[0].approved_to_write
    assert not report.results[0].verified_total_for_quotation
    assert not report.quoted_price_written
    assert not report.gui_actions_performed
    assert "Nie wpisałem żadnej ceny" in research_chat_summary(report)


def test_marketplace_currency_and_shipping_mismatches_remain_visible():
    chat, msg, req = setup()
    report = run(chat, msg, req, FakeProvider((listing(
        currency="EUR", height_mm=2100,
    ),)))
    warnings = report.results[0].warnings
    assert "currency_differs_conversion_not_performed" in warnings
    assert "dimensions_not_proven_equivalent" in warnings
    assert "transport_not_verified_in_price" in warnings


def test_bad_or_invented_provider_result_is_quarantined():
    chat, msg, req = setup()
    provider = FakeProvider((
        listing(source_url="file:///etc/passwd"),
        listing(observed_price="NaN"),
        listing(),
    ))
    report = run(chat, msg, req, provider)
    assert len(report.results) == 1
    assert "some_provider_results_rejected" in report.reasons


def test_no_matching_product_category_does_not_fabricate_result():
    chat, msg, req = setup()
    report = run(chat, msg, req, FakeProvider((
        listing(comparable_category="garage_door"),
    )))
    assert report.status == ResearchStatus.NO_MATCH
    assert report.results == ()
    assert "Cena pozostaje nieustalona" in research_chat_summary(report)


def test_user_message_during_slow_search_discards_obsolete_results():
    chat, msg, req = setup()
    provider = FakeProvider((listing(),))
    provider.on_search = lambda: chat.user_message(
        "Nie, jednak zmień kolor i nie wyceniaj panelu"
    )
    report = run(chat, msg, req, provider)
    assert report.status == ResearchStatus.REQUIRES_REVIEW
    assert report.results == ()
    assert "mission_changed_during_price_search" in report.reasons


def test_old_human_message_cannot_research_after_new_revision():
    chat, msg, req = setup()
    chat.user_message("Wróć do pracy bez szukania ceny")
    provider = FakeProvider((listing(),))
    with pytest.raises(ValueError, match="current_human_message"):
        run(chat, msg, req, provider)
    assert provider.calls == []


def test_untrusted_provider_error_returns_safe_unavailable_result():
    chat, msg, req = setup()

    class BrokenProvider:
        def search(self, query):
            raise RuntimeError("network failure with private customer data")

    report = run(chat, msg, req, BrokenProvider())
    assert report.status == ResearchStatus.NOT_AVAILABLE
    assert report.reasons == ("trusted_search_provider_failed",)
    assert report.results == ()
    assert "private" not in str(report)


def test_bounded_search_ignores_excess_results():
    chat, msg, req = setup()
    report = run(chat, msg, req, FakeProvider(tuple(listing() for _ in range(40))))
    assert len(report.results) == 8


def test_no_user_message_private_document_or_goal_exposed_in_query():
    chat, msg, req = setup("Znajdź cenę drzwi dla prywatnego klienta 123456")
    provider = FakeProvider((listing(),))
    run(chat, msg, req, provider)
    sent = provider.calls[0]
    assert "123456" not in repr(sent)
    assert "OFR/101" not in repr(sent)
    assert sent.category == "door_panel"


def test_query_length_is_bounded_before_any_network_access():
    chat, msg, _ = setup()
    provider = FakeProvider((listing(),))
    req = PriceResearchRequest("x" * 100, True)
    with pytest.raises(ValueError, match="price_search_query_too_long"):
        run(chat, msg, req, provider)
    assert provider.calls == []


def test_provider_malformed_response_does_not_cause_untrusted_execution():
    chat, msg, req = setup()
    report = run(chat, msg, req, FakeProvider("not a tuple of results"))
    assert report.status == ResearchStatus.REQUIRES_REVIEW
    assert report.results == ()


def test_unrelated_type_cannot_claim_it_authorized_research():
    chat, msg, _ = setup()
    provider = FakeProvider((listing(),))
    req = PriceResearchRequest("door_panel", "True")
    with pytest.raises(ValueError, match="requires_salesperson_opt_in"):
        run(chat, msg, req, provider)
    assert provider.calls == []


def test_source_price_and_warnings_are_explained_inside_chat():
    chat, msg, req = setup()
    report = run(chat, msg, req, FakeProvider((listing(),)))
    reply = compose_price_research_chat_reply(report)
    assert "840.00 PLN" in reply
    assert "https://www.example.org/items/123" in reply
    assert "Nie wpisałem żadnej ceny" in reply
    assert publish_research_to_chat(chat, report)
    assert chat.snapshot().messages[-1].text == reply


def test_older_search_does_not_write_to_conversation_after_new_user_instruction():
    chat, msg, req = setup()
    report = run(chat, msg, req, FakeProvider((listing(),)))
    chat.user_message("Nie szukaj więcej, przelicz pozycję 2")
    previous = len(chat.snapshot().messages)
    assert not publish_research_to_chat(chat, report)
    assert len(chat.snapshot().messages) == previous


def test_wrong_offer_cannot_receive_price_research_report():
    chat, msg, req = setup()
    report = run(chat, msg, req, FakeProvider((listing(),)))
    another, _, _ = setup()
    another.document_key = "OFR/OTHER"
    with pytest.raises(ValueError, match="research_document_mismatch"):
        publish_research_to_chat(another, report)
