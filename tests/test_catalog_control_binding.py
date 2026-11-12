from unittest.mock import MagicMock

import pytest

from app.agent.offers.catalog_control_binding import bind_catalog_choice
from app.agent.offers.pagen_configurator import _select_observed


def option(label="Okno DKR", value="sku-27", disabled=False):
    return dict(label=label, value=value, disabled=disabled)


def test_choice_uses_observed_value_not_requested_label():
    binding = bind_catalog_choice("  OKNO   DKR ", [option()])
    assert binding.status == "bound" and binding.value == "sku-27"


@pytest.mark.parametrize("options", [[], [option(disabled=True)], [option(value="")],
    [option(), option(value="other")], [option(), option(label="Inny produkt")],
    [option(label="Okno DKR Premium")]])
def test_missing_disabled_duplicate_and_similar_options_require_review(options):
    assert bind_catalog_choice("Okno DKR", options).status == "review"


def test_exact_customer_labels_do_not_merge_sa():
    assert bind_catalog_choice("Top Trans", [option("Top Trans S.A.")]).status == "review"


def test_selection_uses_current_options_and_checks_result():
    control = MagicMock()
    control.count.return_value = 1
    control.evaluate.return_value = [option()]
    control.input_value.return_value = "sku-27"
    report = _select_observed(control, "Okno DKR")
    control.select_option.assert_called_once_with(value="sku-27")
    assert report["observed_value"] == "sku-27"


def test_catalog_change_blocks_write():
    control = MagicMock()
    control.count.return_value = 1
    control.evaluate.side_effect = [[option()], [option(value="changed")]]
    with pytest.raises(ValueError, match="zmienił"):
        _select_observed(control, "Okno DKR")
    control.select_option.assert_not_called()


def test_wrong_readback_does_not_report_success():
    control = MagicMock()
    control.count.return_value = 1
    control.evaluate.return_value = [option()]
    control.input_value.return_value = "wrong"
    with pytest.raises(ValueError, match="nie potwierdził"):
        _select_observed(control, "Okno DKR")


@pytest.mark.parametrize("count,visible,enabled", [(2, True, True), (1, False, True), (1, True, False)])
def test_unavailable_or_ambiguous_control_never_selected(count, visible, enabled):
    control = MagicMock()
    control.count.return_value = count
    control.is_visible.return_value = visible
    control.is_enabled.return_value = enabled
    with pytest.raises(ValueError, match="Kontrolka"):
        _select_observed(control, "Okno DKR")
    control.select_option.assert_not_called()
