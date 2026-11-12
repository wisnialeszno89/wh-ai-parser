"""Resolve a requested catalog label against observed options, never a guess."""
from dataclasses import dataclass
import unicodedata


def normalized_label(value):
    if not isinstance(value, str):
        raise ValueError("Etykieta opcji musi być tekstem.")
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


@dataclass(frozen=True)
class CatalogBinding:
    status: str
    requested: str
    value: str | None = None
    label: str | None = None
    reason: str | None = None


def bind_catalog_choice(requested, options):
    """Only an unambiguous, enabled exact label with a unique nonempty value wins."""
    key = normalized_label(requested)
    if not key or not isinstance(options, list):
        raise ValueError("Podaj żądaną opcję i aktualną listę z kontrolki.")
    for option in options:
        if (not isinstance(option, dict) or set(option) != {"label", "value", "disabled"}
                or not isinstance(option["label"], str) or not isinstance(option["value"], str)
                or type(option["disabled"]) is not bool):
            raise ValueError("Nieprawidłowy odczyt listy opcji.")
    matches = [option for option in options if normalized_label(option["label"]) == key]
    if not matches:
        return CatalogBinding("review", requested, reason="Brak żądanej opcji w odczytanym katalogu.")
    if len(matches) != 1:
        return CatalogBinding("review", requested, reason="Żądana etykieta pasuje do kilku opcji.")
    match = matches[0]
    if match["disabled"] or not match["value"]:
        return CatalogBinding("review", requested, reason="Żądana opcja jest wyłączona lub nie ma wartości wyboru.")
    if sum(option["value"] == match["value"] for option in options) != 1:
        return CatalogBinding("review", requested, reason="Wartość wyboru jest współdzielona przez kilka opcji.")
    return CatalogBinding("bound", requested, value=match["value"], label=match["label"])
