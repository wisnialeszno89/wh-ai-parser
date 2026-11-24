"""Contract tests for live-shopping adapter (all HTTP synthetic)."""
from __future__ import annotations

from urllib.parse import parse_qs, urlsplit
import pytest

from app.agent.runtime.navimind_price_search_workflow import PriceSearchQuery
from app.agent.runtime.navimind_serpapi_shopping_provider import (
    ProviderFailure, SerpApiShoppingProvider,
)


def query(**kwargs):
    data = dict(
        category="door_panel", product_code="EK-02-A",
        width_mm=1100, height_mm=2200, requested_currency="PLN",
        max_results=8,
    )
    data.update(kwargs)
    return PriceSearchQuery(**data)


def result(**kwargs):
    data = dict(
        title="Panel drzwiowy EK-02-A 1100x2200",
        source="Sklep przykładowy",
        price="870,00 zł",
        extracted_price=870.0,
        product_link="https://www.google.com/shopping/product/123?gl=pl",
    )
    data.update(kwargs)
    return data


class FakeTransport:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def __call__(self, url, *, timeout):
        self.calls.append((url, timeout))
        return self.payload


def provider(rows=None, payload=None):
    fetch = FakeTransport(payload if payload is not None else {
        "shopping_results": rows if rows is not None else [result()],
    })
    return SerpApiShoppingProvider(api_key="offline-test-secret",
                                  transport=fetch), fetch


def test_valid_shopping_response_yields_evidence_limited_reference():
    client, fetch = provider()
    items = client.search(query())
    assert len(items) == 1
    item = items[0]
    assert item.product_code == "EK-02-A"
    assert (item.width_mm, item.height_mm) == (1100, 2200)
    assert item.observed_price == "870.00"
    assert item.currency == "PLN"
    assert item.includes_vat is None
    assert item.shipping_included is None
    assert item.installation_included is None
    assert item.source_url.startswith("https://")
    url, timeout = fetch.calls[0]
    parts = urlsplit(url)
    args = parse_qs(parts.query)
    assert parts.scheme == "https" and parts.hostname == "serpapi.com"
    assert parts.path == "/search.json"
    assert args["engine"] == ["google_shopping"]
    assert args["gl"] == ["pl"]
    assert "EK-02-A" in args["q"][0]
    assert "OFR/101" not in args["q"][0]
    assert args["num"] == ["8"]
    assert timeout == 12


def test_unverified_product_code_or_dimensions_not_fabricated_from_query():
    client, _ = provider(rows=[result(title="Podobny ozdobny panel do drzwi")])
    item = client.search(query())[0]
    assert item.product_code is None
    assert item.width_mm is None and item.height_mm is None


def test_result_in_other_currency_is_reported_but_not_converted():
    client, _ = provider(rows=[result(
        price="299,00 EUR", extracted_price=299.0
    )])
    item = client.search(query())[0]
    assert item.currency == "EUR"
    assert item.observed_price == "299.00"


@pytest.mark.parametrize("row", [
    result(price="870"),
    result(price="$870"),
    result(extracted_price=None),
    result(extracted_price=0, installment={"price": "90 zł/mo"}),
    result(extracted_price=-3),
    result(extracted_price="NaN"),
    result(product_link="http://example.com"),
    result(product_link="file:///etc/passwd"),
    result(product_link="https://user:pass@example.com"),
    result(source=""),
    result(title=""),
])
def test_unverifiable_or_incomplete_listings_are_not_suggested(row):
    client, _ = provider(rows=[row])
    assert client.search(query()) == ()


def test_more_than_eight_source_results_are_never_processed():
    client, _ = provider(rows=[result() for _ in range(40)])
    assert len(client.search(query())) == 8


@pytest.mark.parametrize("category", [
    "raw_google_query_for_private_customer",
    "https://localhost",
    "invoice_password",
])
def test_only_known_nonpersonal_product_categories_are_searchable(category):
    client, fetch = provider()
    with pytest.raises(ValueError, match="unsupported_public_price_category"):
        client.search(query(category=category))
    assert fetch.calls == []


def test_invalid_code_blocked_before_any_network_request():
    client, fetch = provider()
    with pytest.raises(ValueError, match="invalid_public_product_code"):
        client.search(query(product_code="PRIVATE: customer secret"))
    assert not fetch.calls


def test_missing_api_key_from_environment_fails_closed(monkeypatch):
    monkeypatch.delenv("NAVIMIND_SERPAPI_KEY", raising=False)
    assert SerpApiShoppingProvider.from_environment() is None


def test_environment_key_sets_provider_without_network(monkeypatch):
    monkeypatch.setenv("NAVIMIND_SERPAPI_KEY", "local-only-key")
    client = SerpApiShoppingProvider.from_environment()
    assert client is not None
    assert client.api_key == "local-only-key"


def test_api_error_is_not_quoted_or_leaked():
    client, _ = provider(payload={"error": "Rejected with sensitive key"})
    with pytest.raises(ProviderFailure, match="search_api_provider_error"):
        client.search(query())


def test_provider_rejects_malformed_shopping_results():
    client, _ = provider(payload={"shopping_results": "wrong"})
    with pytest.raises(ProviderFailure, match="search_api_invalid_shopping_results"):
        client.search(query())


def test_live_http_blocks_untrusted_endpoint_before_any_open():
    from app.agent.runtime.navimind_serpapi_shopping_provider import _live_http
    with pytest.raises(ProviderFailure, match="search_api_endpoint_not_allowed"):
        _live_http("https://127.0.0.1/search.json", timeout=1)


def test_safe_provider_has_no_gui_or_save_methods():
    client, _ = provider()
    assert not hasattr(client, "save_offer")
    assert not hasattr(client, "write_price")
    assert not hasattr(client, "execute_desktop")


def test_zero_or_negative_code_length_rejected():
    client, fetch = provider()
    with pytest.raises(ValueError, match="invalid_public_product_code"):
        client.search(query(product_code="a"))
    assert not fetch.calls
