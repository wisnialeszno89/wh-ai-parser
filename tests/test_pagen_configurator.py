import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from urllib.parse import urlencode

import pytest

from app.agent.offers import pagen_configurator as pagen

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "pagen-two-windows.json"


def example_order():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("value", [0, -1, True, "1230", 1230.5])
def test_order_rejects_invalid_dimensions(value):
    order = example_order()
    order["positions"][0]["width_mm"] = value
    with pytest.raises(ValueError, match="width_mm"):
        pagen.PagenOrder.from_dict(order)


def test_request_guard_allows_only_add_row_write():
    route = MagicMock()
    body = urlencode({"_triggering_element_name": "informacje_podstawowe_table_add"}).encode()
    route.request = SimpleNamespace(
        url=pagen.PAGEN_URL + "?ajax_form=1&_wrapper_format=drupal_ajax",
        method="POST",
        resource_type="xhr",
        headers={"content-type": "application/x-www-form-urlencoded"},
        post_data_buffer=body,
    )
    route.fetch.return_value.status = 200
    pagen._guard_request(route)
    route.fetch.assert_called_once_with(max_redirects=0)
    route.fulfill.assert_called_once_with(response=route.fetch.return_value)

    route.reset_mock()
    route.fetch.return_value.status = 307
    pagen._guard_request(route)
    route.abort.assert_called_once_with("blockedbyclient")
    route.fulfill.assert_not_called()

    route.reset_mock()
    route.request.post_data_buffer = b"_triggering_element_name=op"
    pagen._guard_request(route)
    route.abort.assert_called_once_with("blockedbyclient")
    route.fetch.assert_not_called()

    route.reset_mock()
    route.request.post_data_buffer = body
    route.request.url = pagen.PAGEN_URL
    pagen._guard_request(route)
    route.abort.assert_called_once_with("blockedbyclient")
    route.fetch.assert_not_called()


def test_guard_recognizes_drupal_multipart_trigger():
    request = SimpleNamespace(
        url=pagen.PAGEN_URL + "?ajax_form=1",
        method="POST",
        resource_type="xhr",
        headers={"content-type": "multipart/form-data; boundary=test"},
        post_data_buffer=(
            b'--test\r\nContent-Disposition: form-data; name="_triggering_element_name"\r\n\r\n'
            b'informacje_podstawowe_table_add\r\n--test--\r\n'
        ),
    )
    assert pagen._is_add_request(request)


@pytest.mark.parametrize("reset_first_row", [False, True])
def test_fill_resolves_new_rows_and_detects_a_reset(monkeypatch, reset_first_row):
    playwright = pytest.importorskip("playwright.sync_api")
    checks = MagicMock()
    monkeypatch.setattr(playwright, "expect", checks)
    page = MagicMock(url=pagen.PAGEN_URL)
    rows = MagicMock()
    monkeypatch.setattr(pagen, "_rows", lambda page: rows)
    page.get_by_role.return_value.is_visible.return_value = False

    def make_row():
        fields = {label: MagicMock() for label, _ in pagen._NUMBER_FIELDS}
        row = MagicMock()
        type_field = row.get_by_role.return_value

        def select_type(label):
            type_field.input_value.return_value = label

        type_field.select_option.side_effect = select_type
        for control in fields.values():
            control.fill.side_effect = (
                lambda value, control=control: setattr(control.input_value, "return_value", value)
            )
        return row, fields

    first, first_field = make_row()
    replacement, replacement_field = make_row()
    second, second_field = make_row()
    fields = {first: first_field, replacement: replacement_field, second: second_field}
    monkeypatch.setattr(pagen, "_field", lambda row, label: fields[row][label])
    active_rows = [first]
    rows.nth.side_effect = lambda index: active_rows[index]

    def add_row():
        replacement.get_by_role.return_value.input_value.return_value = (
            first.get_by_role.return_value.input_value.return_value
        )
        for label, _ in pagen._NUMBER_FIELDS:
            replacement_field[label].input_value.return_value = first_field[label].input_value.return_value
        if reset_first_row:
            replacement_field["Szerokość [mm]"].input_value.return_value = ""
        active_rows[:] = [replacement, second]

    page.get_by_role.return_value.click.side_effect = add_row
    order = pagen.PagenOrder.from_dict(example_order())

    if reset_first_row:
        with pytest.raises(ValueError, match="Pozycja 1"):
            pagen.fill_pagen_order(page, order)
        second.get_by_role.return_value.select_option.assert_not_called()
    else:
        pagen.fill_pagen_order(page, order)
        second_field["Szerokość [mm]"].fill.assert_called_once_with("1500")
        replacement_field["Szerokość [mm]"].input_value.assert_called()
