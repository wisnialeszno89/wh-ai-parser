"""Vetted SerpApi Google Shopping provider for opt-in NaviMind price research.

Uses Google's Shopping results via the documented, paid SerpApi JSON API.
Never fetches a result URL, handles redirects, installs software or enters a
price in WindowHub. Source data remains *market reference*, not a quote.

A key is supplied only by trusted host configuration/environment. No key
means NO network call. The HTTP transport is injectable for offline tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
import os
import re
import ssl
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, HTTPSHandler

from app.agent.runtime.navimind_price_search_workflow import (
    PriceSearchQuery, ProviderObservation,
)

API_ENDPOINT = "https://serpapi.com/search.json"
MAX_RESPONSE_BYTES = 1_000_000
CATEGORY_TERMS = {
    "door_panel": "panel wypełnienie drzwiowe",
    "garage_door": "brama garażowa",
    "exterior_sill": "parapet zewnętrzny",
    "external_accessory": "akcesoria okienne drzwiowe",
    "door_with_external_panel": "drzwi z panelem",
}


class ProviderFailure(RuntimeError):
    """Stable failure without secrets or data from the provider response."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProviderFailure("search_api_redirect_refused")


def _live_http(url: str, *, timeout: float) -> dict[str, Any]:
    """Only call the exact fixed API host; redirects are never followed."""
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname != "serpapi.com" or parts.path != "/search.json":
        raise ProviderFailure("search_api_endpoint_not_allowed")
    opener = build_opener(HTTPSHandler(context=ssl.create_default_context()), _NoRedirect())
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "NaviMind/1 price-reference"})
    try:
        with opener.open(request, timeout=timeout) as response:
            if response.status != 200:
                raise ProviderFailure("search_api_response_not_ok")
            declared_length = response.headers.get("Content-Length")
            if declared_length:
                try:
                    if int(declared_length) > MAX_RESPONSE_BYTES:
                        raise ProviderFailure("search_api_response_too_large")
                except ValueError as exc:
                    raise ProviderFailure("search_api_invalid_length") from exc
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except ProviderFailure:
        raise
    except (OSError, HTTPError, URLError, TimeoutError) as exc:
        # No exception body, URL or credential is exposed.
        raise ProviderFailure("search_api_unavailable") from None
    if len(body) > MAX_RESPONSE_BYTES:
        raise ProviderFailure("search_api_response_too_large")
    try:
        obj = json.loads(body.decode("utf-8"))
    except (UnicodeError, ValueError):
        raise ProviderFailure("search_api_invalid_json") from None
    if not isinstance(obj, dict):
        raise ProviderFailure("search_api_invalid_payload")
    return obj


def _as_price(value: Any) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    try:
        # Decimal(str(float)) avoids binary float arithmetic in string output.
        n = Decimal(str(value))
    except (ValueError, InvalidOperation):
        return None
    if not n.is_finite() or n <= 0:
        return None
    return format(n.quantize(Decimal("0.01")), "f")


def _currency_for_display(price: str, currency_requested: str) -> str | None:
    """Currency must be explicit in the displayed price, never inferred from gl."""
    value = price.casefold()
    tokens = {
        "PLN": (r"(?<!\w)pln(?!\w)", r"zł"),
        "EUR": (r"(?<!\w)eur(?!\w)", r"€"),
        "USD": (r"(?<!\w)usd(?!\w)", r"us\$"),
        "GBP": (r"(?<!\w)gbp(?!\w)", r"£"),
    }
    matched = [code for code, patterns in tokens.items()
               if any(re.search(pattern, value) for pattern in patterns)]
    return matched[0] if len(matched) == 1 else None


def _observed_model(title: str, wanted: str | None) -> str | None:
    if not wanted:
        return None
    # Only claim product code when bounded by separators, never from the
    # query or the entire result payload as an assumption.
    escaped = re.escape(wanted)
    if re.search(r"(?<![\w-])" + escaped + r"(?![\w-])", title, flags=re.I):
        return wanted
    return None


def _observed_dimensions(title: str, width: int | None, height: int | None) -> tuple[int | None, int | None]:
    if width is None or height is None:
        return None, None
    # Dimension matches are only attributed when explicitly present in the
    # product title (not merely in our search query).
    template = rf"(?<!\d){width}\s*[x×]\s*{height}(?!\d)"
    if re.search(template, title, re.I):
        return width, height
    return None, None


def _safe_result_url(raw: Any) -> str | None:
    if not isinstance(raw, str) or len(raw) > 1800:
        return None
    parts = urlsplit(raw)
    if (parts.scheme != "https" or not parts.hostname
            or parts.username or parts.password
            or parts.hostname.lower() in ("localhost", "127.0.0.1")):
        return None
    # We DO NOT fetch user-controlled URLs. This is source display only.
    return raw


@dataclass(frozen=True)
class SerpApiShoppingProvider:
    api_key: str
    transport: Callable[..., dict[str, Any]] = _live_http
    timeout_seconds: float = 12.0

    def __post_init__(self):
        if not isinstance(self.api_key, str) or not self.api_key.strip():
            raise ValueError("search_api_key_required")
        if not (isinstance(self.timeout_seconds, (int, float))
                and 1 <= self.timeout_seconds <= 25):
            raise ValueError("invalid_search_api_timeout")

    @classmethod
    def from_environment(cls) -> "SerpApiShoppingProvider | None":
        key = os.environ.get("NAVIMIND_SERPAPI_KEY", "").strip()
        return cls(api_key=key) if key else None

    def search(self, query: PriceSearchQuery) -> tuple[ProviderObservation, ...]:
        if not isinstance(query, PriceSearchQuery):
            raise ValueError("invalid_price_search_query")
        if query.category not in CATEGORY_TERMS:
            raise ValueError("unsupported_public_price_category")
        if type(query.max_results) is not int or not 1 <= query.max_results <= 8:
            raise ValueError("invalid_result_limit")
        if query.product_code is not None and (
            len(query.product_code) > 80
            or not re.fullmatch(r"[\w.\- ]{2,80}", query.product_code)
        ):
            raise ValueError("invalid_public_product_code")
        for dimension in (query.width_mm, query.height_mm):
            if dimension is not None and (
                type(dimension) is not int or not 1 <= dimension <= 100000
            ):
                raise ValueError("invalid_public_dimension")
        if query.requested_currency not in ("PLN", "EUR"):
            raise ValueError("unsupported_public_currency")
        terms = [CATEGORY_TERMS[query.category]]
        if query.product_code:
            terms.append(query.product_code)
        if query.width_mm and query.height_mm:
            terms.append(f"{query.width_mm}x{query.height_mm}")
        terms.append("cena")
        params = {
            "engine": "google_shopping",
            "q": " ".join(terms),
            "gl": "pl" if query.requested_currency == "PLN" else "de",
            "hl": "pl" if query.requested_currency == "PLN" else "de",
            "num": str(query.max_results),
            "api_key": self.api_key,
        }
        # Fixed host/engine, no caller-provided URL or redirect.
        endpoint = API_ENDPOINT + "?" + urlencode(params)
        payload = self.transport(endpoint, timeout=self.timeout_seconds)
        if not isinstance(payload, dict):
            raise ProviderFailure("search_api_invalid_payload")
        if payload.get("error"):
            raise ProviderFailure("search_api_provider_error")
        listings = payload.get("shopping_results", [])
        if not isinstance(listings, list):
            raise ProviderFailure("search_api_invalid_shopping_results")
        results = []
        for result in listings[:query.max_results]:
            if not isinstance(result, dict):
                continue
            title, seller, display_price = (result.get("title"),
                                            result.get("source"), result.get("price"))
            if not all(isinstance(v, str) and v.strip() for v in (title, seller, display_price)):
                continue
            # Reject installment-only results and listings with no explicit
            # trustworthy currency indicator.
            if result.get("installment") and result.get("extracted_price") in (0, 0.0, None):
                continue
            currency = _currency_for_display(display_price, query.requested_currency)
            if not currency:
                continue
            price = _as_price(result.get("extracted_price"))
            link = _safe_result_url(result.get("product_link"))
            if price is None or link is None:
                continue
            code = _observed_model(title, query.product_code)
            width, height = _observed_dimensions(title, query.width_mm, query.height_mm)
            results.append(ProviderObservation(
                source_kind="retailer",
                source_url=link,
                seller=seller[:160],
                title=title[:350],
                observed_price=price,
                currency=currency,
                comparable_category=query.category,
                product_code=code,
                width_mm=width,
                height_mm=height,
                # The Shopping search listing alone cannot establish these.
                includes_vat=None,
                shipping_included=None,
                installation_included=None,
            ))
        return tuple(results)
