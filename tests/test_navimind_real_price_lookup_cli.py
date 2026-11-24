"""CLI opt-in contract: no key and no consent produce zero network calls."""
from __future__ import annotations

from datetime import date
from app.agent.runtime.navimind_price_search_workflow import ProviderObservation
from tools.run_navimind_price_lookup import execute, main


class Provider:
    def __init__(self):
        self.calls = 0

    def search(self, query):
        self.calls += 1
        return (
            ProviderObservation(
                source_kind="retailer",
                source_url="https://www.google.com/shopping/product/123",
                seller="Shop testowy",
                title="EK-02-A panel drzwiowy 1100x2200",
                observed_price="750.00", currency="PLN",
                comparable_category="door_panel",
                product_code="EK-02-A", width_mm=1100, height_mm=2200,
            ),
        )


def params(provider, **changes):
    args = dict(
        offer="OFR/101", category="door_panel", code="EK-02-A",
        width=1100, height=2200, currency="PLN",
        research_consent=True, provider=provider,
        today=date(2026, 11, 24),
    )
    args.update(changes)
    return args


def test_no_consent_makes_no_request(capsys):
    provider = Provider()
    status = execute(**params(provider, research_consent=False))
    assert status == 2
    assert provider.calls == 0
    assert "RESEARCH_REFUSED=no_explicit_operator_consent" in capsys.readouterr().out


def test_valid_explicit_request_surfaces_source_not_quote_price(capsys):
    provider = Provider()
    assert execute(**params(provider)) == 0
    output = capsys.readouterr().out
    assert provider.calls == 1
    assert "RESEARCH_STATUS=suggestions" in output
    assert "RESEARCH_RESULTS=1" in output
    assert "750.00 PLN" in output
    assert "AUTOMATIC_PRICE_WRITE=False" in output
    assert "WINDOWHUB_EXECUTED=False" in output


def test_wrong_offer_rejected_before_provider(capsys):
    provider = Provider()
    assert execute(**params(provider, offer="customer-name")) == 2
    assert provider.calls == 0


def test_unrecognized_category_rejected_before_provider():
    provider = Provider()
    assert execute(**params(provider, category="whole_client_prompt")) == 2
    assert provider.calls == 0


def test_missing_env_key_remains_unavailable(monkeypatch, capsys):
    monkeypatch.delenv("NAVIMIND_SERPAPI_KEY", raising=False)
    assert execute(**params(None)) == 3
    result = capsys.readouterr().out
    assert "RESEARCH_STATUS=not_available" in result
    assert "RESEARCH_PROVIDER_INVOKED=False" in result


def test_command_line_requires_explicit_consent(capsys):
    assert main([
        "--offer", "OFR/101", "--category", "door_panel",
        "--code", "EK-02-A",
    ]) == 2
    assert "no_explicit_operator_consent" in capsys.readouterr().out
