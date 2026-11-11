"""Select a uniquely matching glazing record without inventing missing attributes."""

from decimal import Decimal, InvalidOperation

_FIELDS = {"panes", "thickness_mm", "ug", "warm_edge", "spacer"}


def _normalize(field, value):
    if field in ("panes", "thickness_mm"):
        if type(value) is not int or value <= 0:
            raise ValueError(f"Pole {field} wymaga dodatniej liczby całkowitej.")
        return value
    if field == "ug":
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            raise ValueError("Ug wymaga dodatniej liczby.")
        try:
            number = Decimal(str(value).replace(",", "."))
        except InvalidOperation:
            raise ValueError("Ug wymaga dodatniej liczby.") from None
        if not number.is_finite() or number <= 0:
            raise ValueError("Ug wymaga dodatniej liczby.")
        return number
    if field == "warm_edge":
        if type(value) is not bool:
            raise ValueError("Stan ciepłej ramki musi być jednoznaczny.")
        return value
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Podaj nazwę ramki.")
    return " ".join(value.casefold().split())


def select_glass_package(requirements, candidates):
    """Require equality for each supplied attribute and a single possible record."""
    if not isinstance(requirements, dict) or not requirements or set(requirements) - _FIELDS:
        raise ValueError("Podaj znane wymagania pakietu szybowego.")
    desired = {key: _normalize(key, value) for key, value in requirements.items()}
    if not isinstance(candidates, list):
        raise ValueError("Oczekiwano listy dostępnych pakietów.")
    matches, unresolved, rejected = [], [], []
    identifiers = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("Nieprawidłowy rekord pakietu.")
        identifier = candidate.get("id")
        if not isinstance(identifier, str) or not identifier.strip() or identifier.strip() in identifiers:
            raise ValueError("Pakiety muszą mieć unikalne identyfikatory.")
        identifiers.add(identifier.strip())
        differences, unknown = [], []
        for field, expected in desired.items():
            actual = candidate.get(field)
            if actual is None:
                unknown.append(field)
            elif _normalize(field, actual) != expected:
                differences.append(field)
        if differences:
            rejected.append({"id": identifier, "different_fields": differences})
        elif unknown:
            unresolved.append({"id": identifier, "missing_fields": unknown})
        else:
            matches.append(candidate)
    report = {
        "status": "review", "requirements": dict(requirements),
        "matching_ids": [item["id"] for item in matches],
        "unresolved": unresolved, "rejected": rejected,
    }
    if len(matches) == 1 and not unresolved:
        report.update(status="selected", selected=dict(matches[0]))
    else:
        report["reason"] = "Brak jednoznacznego pakietu. Zachowaj wymagania do doboru przez handlowca."
    return report
