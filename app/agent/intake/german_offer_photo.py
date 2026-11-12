"""Extract a technical draft from a photographed German window offer table."""

import csv
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from statistics import median

_HEADER = re.compile(r"^(\d+\.\d+)\s+(\d+)\s*Stk\.?\s*(.*)$", re.IGNORECASE)
_PRODUCT = re.compile(r"(.+?)\s*-\s*Fenster\s+(EP)", re.IGNORECASE)
_DIMENSION = re.compile(r"^([BH]):\s*([1-9]\d*)\s*mm\b", re.IGNORECASE)
_STRIP = re.compile(
    r"Abdeckstreifen:\s*Aluminium\s+au(?:ß|ss|b|f)en,\s*(3|4)-seitig,\s*(\d+\s*x\s*\d+)\s*mm",
    re.IGNORECASE,
)


def read_german_offer_photo_file(path: Path, *, tesseract: str = "tesseract") -> dict:
    if not path.is_file():
        raise ValueError(f"Brak pliku zdjęcia: {path}")
    executable = shutil.which(tesseract)
    if not executable:
        raise ValueError("Nie znaleziono Tesseract. Użyj --tesseract ze ścieżką do tesseract.exe.")
    result = subprocess.run(
        [executable, str(path.resolve()), "stdout", "--psm", "11", "-l", "eng", "tsv"],
        check=True, capture_output=True, encoding="utf-8", timeout=60,
    )
    return read_german_offer_photo(result.stdout)


@dataclass(frozen=True)
class _Word:
    left: int
    center: float
    height: int
    text: str


def _ocr_lines(tsv: str) -> tuple[list[tuple[float, str]], float]:
    words = [
        _Word(int(row["left"]), int(row["top"]) + int(row["height"]) / 2, int(row["height"]), row["text"].strip())
        for row in csv.DictReader(tsv.splitlines(), delimiter="\t", quoting=csv.QUOTE_NONE)
        if row["level"] == "5" and row["text"].strip()
    ]
    if not words:
        raise ValueError("OCR nie znalazł tekstu w tabeli.")
    line_height = median(word.height for word in words)
    groups: list[list[_Word]] = []
    for word in sorted(words, key=lambda word: word.center):
        if not groups or word.center - groups[-1][0].center > line_height / 2:
            groups.append([])
        groups[-1].append(word)
    lines = [
        (median(word.center for word in group), " ".join(word.text for word in sorted(group, key=lambda word: word.left)))
        for group in groups
    ]
    return lines, line_height


def read_german_offer_photo(tsv: str) -> dict:
    """Use OCR word coordinates to keep dimensions and details on their own rows."""
    lines, line_height = _ocr_lines(tsv)
    headers = []
    for index, (center, line) in enumerate(lines):
        if re.search(r"\bStk\b", line, re.IGNORECASE):
            match = _HEADER.fullmatch(line)
            if not match:
                raise ValueError(f"Nieczytelny nagłówek pozycji: {line}")
            headers.append((index, center, match.groups()))
    if not headers:
        raise ValueError("Nie znaleziono pozycji z ilością w sztukach.")
    if any(line.upper() in {"DKL", "DKR", "F004 DK-FENSTER"} or _STRIP.fullmatch(line)
           for _, line in lines[:headers[0][0]]):
        raise ValueError("OCR znalazł dane przed pierwszym czytelnym nagłówkiem pozycji.")

    positions, excluded = [], []
    seen = set()
    for offset, (index, center, (position, quantity_text, title)) in enumerate(headers):
        if position in seen:
            raise ValueError(f"Powtórzony numer pozycji {position}.")
        seen.add(position)
        quantity = int(quantity_text)
        if quantity == 0:
            excluded.append({"position": position, "reason": "zero_quantity"})
            continue

        end = headers[offset + 1][0] if offset + 1 < len(headers) else len(lines)
        details = [line for _, line in lines[index + 1:end]]
        product = _PRODUCT.fullmatch(title)
        dimensions = [
            match.groups()
            for y, line in lines
            if abs(y - center) <= 1.5 * line_height
            if (match := _DIMENSION.match(line))
        ]
        opening = [line.upper() for line in details if line.upper() in {"DKL", "DKR"}]
        strips = [match.groups() for line in details if (match := _STRIP.fullmatch(line))]
        notes = [line.upper().replace("WKU", "WKÜ") for line in details if line.upper() in {"WKU", "WKÜ", "SZ"}]
        if (
            not product
            or sorted(axis.upper() for axis, _ in dimensions) != ["B", "H"]
            or sum(line.upper() == "F004 DK-FENSTER" for line in details) != 1
            or len(opening) != 1
            or len(strips) != 1
            or len(notes) != 1
            or any(re.search(r"\bVARIANTE\b", line, re.IGNORECASE) for line in [title, *details])
        ):
            raise ValueError(f"Pozycja {position}: OCR nie potwierdził wszystkich danych aktywnego okna F004.")

        size = {axis.upper(): int(value) for axis, value in dimensions}
        sides, strip_size = strips[0]
        positions.append({
            "position": position,
            "quantity": quantity,
            "width_mm": size["B"],
            "height_mm": size["H"],
            "system": product.group(1),
            "header_code": product.group(2).upper(),
            "construction": "F004 DK-Fenster",
            "opening": opening[0],
            "cover_strip": {
                "material": "Aluminium",
                "side": "outside",
                "sides": int(sides),
                "size_mm": re.sub(r"\s", "", strip_size),
            },
            "note_code": notes[0],
        })
    if not positions:
        raise ValueError("W tabeli brak aktywnych pozycji.")
    return {"status": "technical_draft", "positions": positions, "excluded": excluded}
