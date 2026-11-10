"""Apply window positions to the public PAGEN form and verify its readback."""

from __future__ import annotations

import re
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from urllib.parse import parse_qs, urlsplit

from app.agent.offers.windowhub_position_mission import WindowPositionRequest

PAGEN_URL = "https://pagen.pl/pl/konfigurator-wyceny-okien"
_ADD_LABEL = "Dodaj kolejne okno"
_ADD_TRIGGER = "informacje_podstawowe_table_add"
_NUMBER_FIELDS = (
    ("Ilość", "quantity"),
    ("Szerokość [mm]", "width_mm"),
    ("Wysokość [mm]", "height_mm"),
)


@dataclass(frozen=True)
class PagenPosition:
    window_type: str
    dimensions: WindowPositionRequest


@dataclass(frozen=True)
class PagenOrder:
    profile: str
    positions: tuple[PagenPosition, ...]

    @classmethod
    def from_dict(cls, data: object) -> PagenOrder:
        if not isinstance(data, dict) or data.keys() != {"profile", "positions"}:
            raise ValueError("Zlecenie musi zawierać pola profile i positions.")
        profile, positions = data["profile"], data["positions"]
        if not isinstance(profile, str) or not profile.strip():
            raise ValueError("Brakuje nazwy profilu.")
        if not isinstance(positions, list) or not 1 <= len(positions) <= 10:
            raise ValueError("Podaj od 1 do 10 pozycji.")
        rows = []
        for number, row in enumerate(positions, 1):
            if not isinstance(row, dict) or row.keys() != {"window_type", "quantity", "width_mm", "height_mm"}:
                raise ValueError(f"Pozycja {number} ma nieprawidłowe pola.")
            name = row["window_type"]
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"Brakuje typu okna w pozycji {number}.")
            dimensions = WindowPositionRequest(row["quantity"], row["width_mm"], row["height_mm"])
            rows.append(PagenPosition(name.strip(), dimensions))
        return cls(profile.strip(), tuple(rows))


def _is_add_request(request) -> bool:
    url = urlsplit(request.url)
    if (
        request.method != "POST"
        or request.resource_type not in {"xhr", "fetch"}
        or url._replace(query="", fragment="").geturl() != PAGEN_URL
        or parse_qs(url.query).get("ajax_form") != ["1"]
    ):
        return False
    content_type = request.headers.get("content-type", "")
    body = request.post_data_buffer or b""
    if content_type.startswith("application/x-www-form-urlencoded"):
        triggers = parse_qs(body.decode("utf-8", errors="replace")).get("_triggering_element_name", [])
    elif content_type.startswith("multipart/form-data"):
        message = BytesParser(policy=policy.default).parsebytes(
            b"Content-Type: " + content_type.encode("ascii") + b"\r\n\r\n" + body
        )
        triggers = [
            part.get_content().strip()
            for part in message.iter_parts()
            if part.get_param("name", header="Content-Disposition") == "_triggering_element_name"
        ]
    else:
        return False
    return triggers == [_ADD_TRIGGER]


def _guard_request(route) -> None:
    request = route.request
    if _is_add_request(request):
        response = route.fetch(max_redirects=0)
        if 300 <= response.status < 400:
            route.abort("blockedbyclient")
        else:
            route.fulfill(response=response)
    elif request.method in {"GET", "HEAD", "OPTIONS"}:
        route.continue_()
    else:
        route.abort("blockedbyclient")


def _rows(page):
    quantity = page.get_by_role("spinbutton", name="Ilość", exact=True)
    return page.get_by_role("row").filter(has=quantity)


def _field(row, label):
    return row.get_by_role("spinbutton", name=label, exact=True)


def _verify_rows(page, positions: tuple[PagenPosition, ...]) -> None:
    rows = _rows(page)
    for index, position in enumerate(positions):
        row = rows.nth(index)
        expected = [position.window_type]
        actual = [row.get_by_role("combobox").input_value()]
        for label, attribute in _NUMBER_FIELDS:
            expected.append(str(getattr(position.dimensions, attribute)))
            actual.append(_field(row, label).input_value())
        if actual != expected:
            raise ValueError(f"Pozycja {index + 1} różni się od zlecenia. Odczytano {actual!r}, oczekiwano {expected!r}.")


def fill_pagen_order(page, order: PagenOrder) -> None:
    """Fill a fresh isolated page. Only the add-row AJAX POST may leave it."""
    from playwright.sync_api import expect

    page.context.route("**/*", _guard_request)
    page.goto(PAGEN_URL)
    if page.url != PAGEN_URL:
        raise ValueError("Otwarta strona nie odpowiada konfiguratorowi PAGEN.")

    reject = page.get_by_role("button", name=re.compile(r"odrzuć|deny all|reject all", re.I))
    if reject.is_visible():
        reject.click()

    profile = page.get_by_role("combobox", name="Wybierz profil okien", exact=True)
    profile.select_option(label=order.profile)
    rows = _rows(page)
    expect(rows).to_have_count(1)
    add = page.get_by_role("button", name=_ADD_LABEL, exact=True)
    for index, position in enumerate(order.positions):
        if index:
            add.click()
            expect(rows).to_have_count(index + 1)
            _verify_rows(page, order.positions[:index])
        row = rows.nth(index)
        row.get_by_role("combobox").select_option(label=position.window_type)
        for label, attribute in _NUMBER_FIELDS:
            _field(row, label).fill(str(getattr(position.dimensions, attribute)))

    expect(rows).to_have_count(len(order.positions))
    expect(profile).to_have_value(order.profile)
    _verify_rows(page, order.positions)
