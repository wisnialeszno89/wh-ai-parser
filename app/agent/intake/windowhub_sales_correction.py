"""Read a bounded Polish correction command and resolve exact offer/position identity."""

from copy import deepcopy
from decimal import Decimal
import re
import unicodedata

_COMMAND = re.compile(
    r"w\s+ofercie\s+(?P<offer>[\w/-]+)\s+zmien\s+pozycje\s+(?P<position>\d+(?:\.\d+)?)"
    r"\s+na\s+(?P<width>[1-9]\d*)\s*[x×]\s*(?P<height>[1-9]\d*)(?:\s*mm)?"
    r"(?:\s*,\s*slup(?:ek)?\s+(?P<mullion>ruchomy|staly))?"
    r"(?:\s*,\s*(?P<active>lewe|prawe)(?:\s+skrzydlo)?\s+czynne)?"
    r"(?:\s*,\s*podzial\s+(?P<split>[1-9]\d*)\s*mm\s+od\s+lewej)?[.!]?",
    re.IGNORECASE,
)


def parse_sales_correction(text):
    if not isinstance(text, str) or not text.strip() or len(text) > 2000:
        raise ValueError("Podaj jedno polecenie korekty do 2000 znaków.")
    normalized = unicodedata.normalize("NFKD", text.replace("ł", "l").replace("Ł", "L"))
    normalized = "".join(character for character in normalized if not unicodedata.combining(character))
    match = _COMMAND.fullmatch(normalized.strip())
    if not match:
        raise ValueError("Nie rozpoznano całego polecenia. Użyj formatu z numerem oferty, pozycji i wymiarami.")
    values = match.groupdict()
    return {
        "offer": values["offer"], "position": values["position"],
        "width_mm": int(values["width"]), "height_mm": int(values["height"]),
        "mullion": {"ruchomy": "movable", "staly": "fixed"}.get((values["mullion"] or "").lower()),
        "active_side": {"lewe": "left", "prawe": "right"}.get((values["active"] or "").lower()),
        "split_from_left_mm": int(values["split"]) if values["split"] else None,
    }


def resolve_sales_correction(text, offers):
    request = parse_sales_correction(text)
    number = request["offer"].casefold()
    matches = [offer for offer in offers if offer["number"].casefold() == number]
    if not matches and number.isdigit():
        matches = [offer for offer in offers if offer["number"].rsplit("/", 1)[-1].isdigit()
                   and int(offer["number"].rsplit("/", 1)[-1]) == int(number)]
    if len(matches) != 1:
        raise ValueError("Numer oferty nie wskazuje jednego rekordu.")
    offer = matches[0]
    reference = Decimal(request["position"])
    rows = [row for row in offer["positions"]
            if re.fullmatch(r"\d+(?:\.\d+)?", row["reference"]) and Decimal(row["reference"]) == reference]
    if len(rows) != 1:
        raise ValueError("Numer pozycji nie wskazuje jednego rekordu.")
    row = rows[0]
    specification = deepcopy(row["specification"])
    kind = row["kind"]
    if request["mullion"] is not None:
        kind = "stulp" if request["mullion"] == "movable" else "double_fixed"
        specification["mullion"] = request["mullion"]
    if request["active_side"] is not None:
        if kind != "stulp":
            raise ValueError("Skrzydło czynne wymaga konstrukcji ze słupkiem ruchomym.")
        specification["active_side"] = request["active_side"]
    if kind == "stulp":
        active = specification.get("active_side")
        if active not in ("left", "right"):
            raise ValueError("Podaj skrzydło czynne dla słupka ruchomego.")
        # Keep the existing fitting direction on the requested active sash.
        specification = {key: value for key, value in specification.items()
                         if key in ("mullion", "active_side", "glazing_panes", "split_from_left_mm", f"{active}_opening")}
    elif kind == "double_fixed":
        specification.pop("active_side", None)
    if request["split_from_left_mm"] is not None:
        if kind == "single":
            raise ValueError("Jednoskrzydłowa konstrukcja nie ma podziału na dwa pola.")
        specification["split_from_left_mm"] = request["split_from_left_mm"]
    elif kind != "single" and request["width_mm"] != row["width_mm"]:
        raise ValueError("Przy zmianie szerokości podaj podział w mm od lewej.")
    return {
        "offer_number": offer["number"], "position_reference": row["reference"],
        "changes": {"kind": kind, "width_mm": request["width_mm"], "height_mm": request["height_mm"],
                    "specification": specification},
        "command": text, "parsed_request": request,
    }
