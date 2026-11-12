"""Read structured PAGEN orders from a Polish table or the original JSON."""

import csv
import json
from pathlib import Path

from app.agent.offers.pagen_configurator import PagenOrder

_CSV_COLUMNS = ("Profil", "Typ okna", "Ilość", "Szerokość [mm]", "Wysokość [mm]")


def read_pagen_order(path: Path) -> PagenOrder:
    if path.suffix.casefold() != ".csv":
        return PagenOrder.from_dict(json.loads(path.read_text(encoding="utf-8-sig")))

    positions = []
    profile = ""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.reader(stream, delimiter=";", strict=True)
        header = next(rows, ())
        if [cell.strip().casefold() for cell in header] != [name.casefold() for name in _CSV_COLUMNS]:
            raise ValueError(f"Oczekiwany nagłówek CSV: {';'.join(_CSV_COLUMNS)}")

        for row in rows:
            if not row:
                continue
            if len(row) != len(_CSV_COLUMNS):
                raise ValueError(f"Wiersz {rows.line_num}: oczekiwano pięciu kolumn.")
            row_profile, window_type, *numbers = (cell.strip() for cell in row)
            if not row_profile or not window_type:
                raise ValueError(f"Wiersz {rows.line_num}: wpisz profil i typ okna.")
            if profile and profile != row_profile:
                raise ValueError(f"Wiersz {rows.line_num}: wszystkie pozycje muszą mieć ten sam profil.")
            if any(not (value.isascii() and value.isdecimal()) for value in numbers):
                raise ValueError(f"Wiersz {rows.line_num}: podaj całkowitą ilość i wymiary w mm.")
            quantity, width, height = map(int, numbers)
            if min(quantity, width, height) <= 0:
                raise ValueError(f"Wiersz {rows.line_num}: ilość i wymiary muszą być większe od zera.")
            profile = row_profile
            positions.append(dict(window_type=window_type, quantity=quantity, width_mm=width, height_mm=height))

    return PagenOrder.from_dict(dict(profile=profile, positions=positions))
