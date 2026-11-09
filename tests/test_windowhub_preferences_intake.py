import pytest

from app.agent.intake.windowhub_preferences import read_excluded_prices
from tools.live_windowhub_new_offer_mission import main


TABLE = (
    "Opcja;Zaznaczone\n"
    "Bez ceny demontażu;TAK\n"
    "Bez ceny montażu;NIE\n"
    "Bez ceny konstrukcji;NIE\n"
    "Bez ceny wykończenia;TAK\n"
)


def test_order_table_is_validated_offline_and_reports_checkbox_states(tmp_path, capsys):
    path = tmp_path / "preferencje.csv"
    path.write_text(TABLE, encoding="utf-8-sig")
    assert read_excluded_prices(path) == ("removal", "finishing")
    assert main(["--preferences-file", str(path), "--inspect-preferences"]) == 0
    output = capsys.readouterr().out
    assert "Bez ceny montażu: odznacz" in output
    assert "Bez ceny demontażu: zaznacz" in output
    assert "OFFER_PREFERENCES_RESULT=table_validated" in output


@pytest.mark.parametrize("table", [
    TABLE.replace("Bez ceny montażu;NIE\n", ""),
    TABLE + "Bez ceny konstrukcji;TAK\n",
    TABLE.replace("Bez ceny demontażu;TAK", "Bez ceny demontażu;?"),
    TABLE.replace("Bez ceny demontażu;TAK", "Rabaty;TAK"),
])
def test_incomplete_ambiguous_or_unknown_orders_are_rejected(tmp_path, table):
    path = tmp_path / "preferencje.csv"
    path.write_text(table, encoding="utf-8")
    with pytest.raises(ValueError):
        read_excluded_prices(path)
