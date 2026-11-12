"""Apply window positions to the public PAGEN form and verify its readback."""

from __future__ import annotations

import re
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from urllib.parse import parse_qs, urlsplit

from app.agent.offers.windowhub_position_mission import WindowPositionRequest
from app.agent.offers.catalog_control_binding import bind_catalog_choice

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
    color: str | None = None
    glazing: str | None = None

    def to_dict(self):
        data = {"profile": self.profile, "positions": [
            {"window_type": position.window_type,
             **{attribute: getattr(position.dimensions, attribute) for _, attribute in _NUMBER_FIELDS}}
            for position in self.positions]}
        for key in ("color", "glazing"):
            if getattr(self, key) is not None:
                data[key] = getattr(self, key)
        return data

    @classmethod
    def from_dict(cls, data: object) -> PagenOrder:
        if not isinstance(data, dict) or not {"profile", "positions"} <= data.keys() or data.keys() - {"profile", "positions", "color", "glazing"}:
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
        shared = {}
        for key in ("color", "glazing"):
            value = data.get(key)
            if key in data and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"Pole {key} wymaga dokładnej nazwy opcji z katalogu.")
            shared[key] = value.strip() if value is not None else None
        return cls(profile.strip(), tuple(rows), **shared)


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


_READ_OPTIONS = """el => Array.from(el.options).map(o => ({
    label: o.label, value: o.value,
    disabled: !!o.disabled || !!o.closest('optgroup[disabled]')
}))"""


def _select_observed(control, requested):
    if control.count() != 1 or not control.is_visible() or not control.is_enabled():
        raise ValueError("Kontrolka wyboru nie jest jednoznaczna, widoczna i dostępna.")
    options = control.evaluate(_READ_OPTIONS)
    binding = bind_catalog_choice(requested, options)
    if binding.status != "bound":
        raise ValueError(f"{requested}: {binding.reason}")
    # Re-read before input: a changing catalog invalidates the prepared choice.
    if control.evaluate(_READ_OPTIONS) != options or not control.is_enabled():
        raise ValueError("Katalog zmienił się przed wyborem. Odczytaj formularz ponownie.")
    control.select_option(value=binding.value)
    if control.input_value() != binding.value:
        raise ValueError("Odczyt kontrolki nie potwierdził wybranej opcji.")
    return {"requested": requested, "observed_label": binding.label, "observed_value": binding.value}


def _verify_rows(page, positions: tuple[PagenPosition, ...]) -> list[dict]:
    rows = _rows(page)
    verified = []
    for index, position in enumerate(positions):
        row = rows.nth(index)
        type_control = row.get_by_role("combobox")
        binding = bind_catalog_choice(position.window_type, type_control.evaluate(_READ_OPTIONS))
        if binding.status != "bound":
            raise ValueError(f"Pozycja {index + 1}: katalog nie potwierdza typu okna.")
        expected = [binding.value]
        actual = [type_control.input_value()]
        for label, attribute in _NUMBER_FIELDS:
            expected.append(str(getattr(position.dimensions, attribute)))
            actual.append(_field(row, label).input_value())
        if actual != expected:
            raise ValueError(f"Pozycja {index + 1} różni się od zlecenia. Odczytano {actual!r}, oczekiwano {expected!r}.")
        verified.append({"position": index + 1,
                         "requested": {"window_type": position.window_type,
                                       **{attribute: getattr(position.dimensions, attribute) for _, attribute in _NUMBER_FIELDS}},
                         "observed": {"window_type_label": binding.label, "window_type_value": actual[0],
                                      **{attribute: int(actual[number + 1]) for number, (_, attribute) in enumerate(_NUMBER_FIELDS)}}})
    return verified


_SHARED_FIELDS = {"color": "Kolor", "glazing": "Szyba"}


def _shared_control(page, key):
    return page.get_by_role("combobox", name=_SHARED_FIELDS[key], exact=True)


def _observe_catalog(control):
    if control.count() != 1 or not control.is_visible():
        raise ValueError("Lista katalogowa nie jest jednoznaczna i widoczna.")
    options = control.evaluate(_READ_OPTIONS)
    # Reuse the binding schema validation even for an empty catalog.
    bind_catalog_choice("__catalog_schema_check__", options)
    return {"enabled": bool(control.is_enabled()), "options": options}


def _open_pagen(page):
    page.context.route("**/*", _guard_request)
    page.goto(PAGEN_URL)
    if page.url != PAGEN_URL:
        raise ValueError("Otwarta strona nie odpowiada konfiguratorowi PAGEN.")
    reject = page.get_by_role("button", name=re.compile(r"odrzuć|deny all|reject all", re.I))
    if reject.is_visible():
        reject.click()


def inspect_pagen_catalog(page, profile_label=None):
    """Read current options; optionally select a profile to expose its catalog."""
    _open_pagen(page)
    profile = page.get_by_role("combobox", name="Wybierz profil okien", exact=True)
    profile_evidence = _select_observed(profile, profile_label) if profile_label else None
    fields = {"profile": _observe_catalog(profile),
              "window_type": _observe_catalog(_rows(page).nth(0).get_by_role("combobox"))}
    fields.update({key: _observe_catalog(_shared_control(page, key)) for key in _SHARED_FIELDS})
    return {"status": "catalog_observed", "evidence": "browser_dom_catalog",
            "url": PAGEN_URL, "selected_profile": profile_evidence, "catalog": fields,
            "submitted": False, "wh_offer_created": False}


def _verify_shared(page, order):
    results = {}
    for key in _SHARED_FIELDS:
        requested = getattr(order, key)
        if requested is None:
            results[key] = {"status": "not_requested", "scope": "whole_form"}
            continue
        control = _shared_control(page, key)
        catalog = _observe_catalog(control)
        binding = bind_catalog_choice(requested, catalog["options"])
        actual = control.input_value()
        if not catalog["enabled"] or binding.status != "bound" or actual != binding.value:
            raise ValueError(f"Końcowy odczyt pola {_SHARED_FIELDS[key]} nie odpowiada zleceniu.")
        results[key] = {"status": "verified", "scope": "whole_form", "requested": requested,
                        "observed_label": binding.label, "observed_value": actual}
    return results


def fill_pagen_order(page, order: PagenOrder) -> dict:
    """Fill a fresh isolated page. Only the add-row AJAX POST may leave it."""
    from playwright.sync_api import expect

    _open_pagen(page)

    profile = page.get_by_role("combobox", name="Wybierz profil okien", exact=True)
    profile_evidence = _select_observed(profile, order.profile)
    # Resolve every requested shared option before editing any window rows.
    for key in _SHARED_FIELDS:
        requested = getattr(order, key)
        if requested is not None:
            catalog = _observe_catalog(_shared_control(page, key))
            binding = bind_catalog_choice(requested, catalog["options"])
            if not catalog["enabled"] or binding.status != "bound":
                available = [item["label"] for item in catalog["options"] if not item["disabled"] and item["value"]]
                raise ValueError(f"{_SHARED_FIELDS[key]}: {binding.reason or 'Kontrolka wyłączona.'} Dostępne: {available!r}")
    position_evidence = []
    rows = _rows(page)
    expect(rows).to_have_count(1)
    add = page.get_by_role("button", name=_ADD_LABEL, exact=True)
    for index, position in enumerate(order.positions):
        if index:
            add.click()
            expect(rows).to_have_count(index + 1)
            _verify_rows(page, order.positions[:index])
        row = rows.nth(index)
        type_evidence = _select_observed(row.get_by_role("combobox"), position.window_type)
        for label, attribute in _NUMBER_FIELDS:
            control = _field(row, label)
            if control.count() != 1 or not control.is_visible() or not control.is_enabled():
                raise ValueError(f"Pozycja {index + 1}: pole {label} jest niedostępne lub niejednoznaczne.")
            desired = str(getattr(position.dimensions, attribute))
            control.fill(desired)
            if control.input_value() != desired:
                raise ValueError(f"Pozycja {index + 1}: nie potwierdzono pola {label}.")
        position_evidence.append({"position": index + 1, "type": type_evidence,
                                  **{attribute: getattr(position.dimensions, attribute) for _, attribute in _NUMBER_FIELDS}})

    for key in _SHARED_FIELDS:
        requested = getattr(order, key)
        if requested is not None:
            _select_observed(_shared_control(page, key), requested)
    shared_readback = _verify_shared(page, order)

    expect(rows).to_have_count(len(order.positions))
    expect(profile).to_have_value(profile_evidence["observed_value"])
    readback = _verify_rows(page, order.positions)

    # Catalog and all prior rows are verified again after the last edit.
    final_profile = bind_catalog_choice(order.profile, profile.evaluate(_READ_OPTIONS))
    if final_profile.status != "bound" or profile.input_value() != final_profile.value:
        raise ValueError("Profil zmienił się przed końcowym odczytem.")
    return {"status": "form_verified", "evidence": "browser_dom_readback",
            "url": PAGEN_URL, "profile": profile_evidence, "positions": readback,
            "selection_trace": position_evidence, "shared_options": shared_readback,
            "submitted": False, "wh_offer_created": False,
            "sales_review_required": True}
