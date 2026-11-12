from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.agent.intake.pagen_order import read_pagen_order
from app.agent.offers import pagen_configurator as pagen
from tools.run_pagen_order import choose_catalog_options


def option(label, value, disabled=False):
    return dict(label=label, value=value, disabled=disabled)


def request(**extra):
    return dict(profile="Profil testowy", positions=[dict(window_type="Okno testowe", quantity=2, width_mm=1100, height_mm=1000)], **extra)


def control(options):
    item = MagicMock()
    item.count.return_value = 1
    item.evaluate.return_value = options
    item.input_value.return_value = ""
    item.select_option.side_effect = lambda value: setattr(item.input_value, "return_value", value)
    return item


@pytest.fixture
def form(monkeypatch):
    playwright = pytest.importorskip("playwright.sync_api")
    monkeypatch.setattr(playwright, "expect", MagicMock())
    page = MagicMock(url=pagen.PAGEN_URL)
    profile = control([option("Profil testowy", "prof-81")])
    color = control([option("Biały / Antracyt", "color-18")])
    glazing = control([option("Pakiet trzyszybowy", "glass-48")])
    window_type = control([option("Okno testowe", "type-12")])
    reject = MagicMock()
    reject.is_visible.return_value = False
    add = MagicMock()
    controls = {"Wybierz profil okien": profile, "Kolor": color, "Szyba": glazing}
    def get_by_role(role, **kwargs):
        if role == "combobox":
            return controls[kwargs["name"]]
        return add if kwargs.get("name") == "Dodaj kolejne okno" else reject
    page.get_by_role.side_effect = get_by_role
    fields = {label: control([]) for label, _ in pagen._NUMBER_FIELDS}
    for field in fields.values():
        field.fill.side_effect = lambda value, field=field: setattr(field.input_value, "return_value", value)
    row = MagicMock()
    row.get_by_role.return_value = window_type
    rows = MagicMock()
    rows.nth.return_value = row
    monkeypatch.setattr(pagen, "_rows", lambda page: rows)
    monkeypatch.setattr(pagen, "_field", lambda row, label: fields[label])
    return page, controls, fields


def test_shared_options_are_exact_form_wide_requirements(form):
    page, controls, fields = form
    order = pagen.PagenOrder.from_dict(request(color="Biały / Antracyt", glazing="Pakiet trzyszybowy"))
    result = pagen.fill_pagen_order(page, order)
    controls["Kolor"].select_option.assert_called_once_with(value="color-18")
    controls["Szyba"].select_option.assert_called_once_with(value="glass-48")
    assert result["shared_options"]["color"]["observed_label"] == "Biały / Antracyt"
    assert result["shared_options"]["glazing"]["scope"] == "whole_form"
    assert result["positions"][0]["observed"]["width_mm"] == 1100
    assert result["submitted"] is False


def test_absent_requirements_are_not_mistaken_for_verified_defaults(form):
    page, controls, _ = form
    result = pagen.fill_pagen_order(page, pagen.PagenOrder.from_dict(request()))
    assert result["shared_options"]["color"]["status"] == "not_requested"
    controls["Kolor"].select_option.assert_not_called()
    controls["Szyba"].evaluate.assert_not_called()


def test_missing_option_keeps_request_and_blocks_row_edits(form):
    page, _, fields = form
    order = pagen.PagenOrder.from_dict(request(color="Mahoń / Biały"))
    with pytest.raises(ValueError, match="Dostępne"):
        pagen.fill_pagen_order(page, order)
    assert order.color == "Mahoń / Biały"
    for field in fields.values():
        field.fill.assert_not_called()


def test_selecting_glass_that_resets_color_is_detected(form):
    page, controls, _ = form
    def select_glass(value):
        controls["Szyba"].input_value.return_value = value
        controls["Kolor"].input_value.return_value = "reset"
    controls["Szyba"].select_option.side_effect = select_glass
    with pytest.raises(ValueError, match="Kolor"):
        pagen.fill_pagen_order(page, pagen.PagenOrder.from_dict(request(color="Biały / Antracyt", glazing="Pakiet trzyszybowy")))


def test_shared_change_that_resets_dimensions_is_detected(form):
    page, controls, fields = form
    def select_glass(value):
        controls["Szyba"].input_value.return_value = value
        fields["Szerokość [mm]"].input_value.return_value = "0"
    controls["Szyba"].select_option.side_effect = select_glass
    with pytest.raises(ValueError, match="Pozycja 1"):
        pagen.fill_pagen_order(page, pagen.PagenOrder.from_dict(request(glazing="Pakiet trzyszybowy")))


def test_catalog_inventory_uses_live_lists_without_filling_positions(form):
    page, _, fields = form
    report = pagen.inspect_pagen_catalog(page, "Profil testowy")
    assert report["status"] == "catalog_observed"
    assert report["catalog"]["glazing"]["options"][0]["value"] == "glass-48"
    for field in fields.values():
        field.fill.assert_not_called()


@pytest.mark.parametrize("key,value", [("color", ""), ("glazing", None), ("color", 3), ("glazing", "  ")])
def test_invalid_optional_specification_is_rejected(key, value):
    with pytest.raises(ValueError):
        pagen.PagenOrder.from_dict(request(**{key:value}))


def test_csv_remains_compatible():
    order = read_pagen_order(Path(__file__).resolve().parents[1] / "examples/pagen-two-windows.csv")
    assert order.color is None and order.glazing is None and len(order.positions) == 2


def test_numbered_choice_uses_observed_labels_and_skips_disabled_options():
    field = dict(enabled=True, options=[option("Placeholder", ""), option("Wyłączony", "x", True), option("Dostępny", "code")])
    answers = iter(["1", "0"])
    selected = choose_catalog_options({"catalog":{"color":field, "glazing":field}}, read=lambda prompt:next(answers))
    assert selected == dict(color="Dostępny", glazing=None)


@pytest.mark.parametrize("answer", ["", "-1", "2", "a", "１"])
def test_invalid_numbered_choice_is_rejected(answer):
    field = dict(enabled=True, options=[option("Dostępny", "code")])
    with pytest.raises(ValueError):
        choose_catalog_options({"catalog":{"color":field, "glazing":field}}, read=lambda prompt:answer)


def test_resolved_order_roundtrip_keeps_shared_requirements():
    original = pagen.PagenOrder.from_dict(request(color="Biały / Antracyt", glazing="Pakiet trzyszybowy"))
    assert pagen.PagenOrder.from_dict(original.to_dict()) == original
