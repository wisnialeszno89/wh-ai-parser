"""Read the explicit four-row price preference table before opening WindowHub."""

import csv
from pathlib import Path

from app.agent.offers.windowhub_document_properties_action import DOCUMENT_PRICE_EXCLUSIONS


def read_excluded_prices(path: Path) -> tuple[str, ...]:
    """Read a UTF-8, semicolon-delimited table with Opcja and Zaznaczone columns."""
    if not path.is_file() or path.stat().st_size > 4096:
        raise ValueError("Brak pliku preferencji lub przekroczono 4 KB.")
    fields = {label.casefold(): key for key, label in DOCUMENT_PRICE_EXCLUSIONS.items()}
    states = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.reader(stream, delimiter=";", strict=True)
        header = next(rows, ())
        if [cell.strip().casefold() for cell in header] != ["opcja", "zaznaczone"]:
            raise ValueError("Oczekiwany nagłówek tabeli: Opcja;Zaznaczone.")
        for row in rows:
            if not row:
                continue
            if len(row) != 2:
                raise ValueError(f"Wiersz {rows.line_num}: oczekiwano dwóch kolumn.")
            option, value = (cell.strip().casefold() for cell in row)
            field = fields.get(option)
            if field is None or field in states or value not in {"tak", "nie"}:
                raise ValueError(f"Wiersz {rows.line_num}: nieznana lub powtórzona opcja albo wartość inna niż TAK/NIE.")
            states[field] = value == "tak"
    if states.keys() != DOCUMENT_PRICE_EXCLUSIONS.keys():
        raise ValueError("Tabela musi określać wszystkie cztery opcje cenowe.")
    return tuple(
        key.removeprefix("exclude_").removesuffix("_price")
        for key in DOCUMENT_PRICE_EXCLUSIONS if states[key]
    )
