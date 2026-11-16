"""No desktop actions are executed by plan-only offer tests."""
from tools.run_windowhub_sales_offer_live import main


def test_plan_only_limi_with_requested_finishes(capsys):
    rc = main([
        "--customer-name", "Limi Fensterbau",
        "--width", "1500", "--height", "1400", "--quantity", "1",
        "--color-outside", "antracyt", "--color-inside", "biały",
        "--glazing-panes", "2",
    ])
    output = capsys.readouterr().out
    assert rc == 0
    assert "MISSION_CUSTOMER=Limi Fensterbau" in output
    assert "MISSION_COLORS=antracyt / biały" in output
    assert "MISSION_GLAZING_PANES=2" in output
    assert "construction_visible;installation_hidden;removal_hidden;finishing_hidden" in output
    assert "PLAN_ONLY=True" in output


def test_invalid_customer_name_stops_without_desktop_access():
    assert main(["--customer-name", ""]) == 2


def test_invalid_dimensions_stops_without_desktop_access():
    import pytest
    with pytest.raises(ValueError):
        main(["--customer-name", "Limi Fensterbau", "--width", "0"])
