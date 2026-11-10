"""Extract a review draft from a German invoice with blue X marks by its item descriptions."""

import csv
import io
import re
import shutil
import subprocess

from PIL import Image, ImageOps

_ITEM = re.compile(r"([1-9]\d*)\s+([1-9]\d*)\s+Stk\.?\s+\d{4,}", re.IGNORECASE)
_SIZE = re.compile(r"\b([1-9]\d{2,4})\s*[x×]\s*([1-9]\d{2,4})\s*mm\b", re.IGNORECASE)
_SCREEN = re.compile(r"\bInsektenschutz(rollo|gitter)\b", re.IGNORECASE)
_SCALE = 3


def _ocr(executable, image, mode):
    data = io.BytesIO()
    image.save(data, format="PNG")
    result = subprocess.run(
        [executable, "stdin", "stdout", "--psm", str(mode), "-l", "eng", "tsv"],
        input=data.getvalue(), capture_output=True, check=True, timeout=60,
    )
    return [
        (int(word["left"]), int(word["top"]), int(word["width"]), int(word["height"]), word["text"].strip())
        for word in csv.DictReader(result.stdout.decode("utf-8").splitlines(), delimiter="\t", quoting=csv.QUOTE_NONE)
        if word["level"] == "5" and word["text"].strip()
    ]


def _table_bounds(words):
    headers = ("pos", "anzahl", "einheit", "artikelnr", "bezeichnung")
    matches = [[word for word in words if word[4].lower().rstrip(".") == name] for name in headers]
    if any(len(items) != 1 for items in matches):
        raise ValueError("Nie znaleziono jednoznacznego nagłówka tabeli faktury.")
    columns = [items[0] for items in matches]
    xs = [word[0] for word in columns]
    height = max(word[3] for word in columns)
    if xs != sorted(set(xs)) or max(word[1] for word in columns) - min(word[1] for word in columns) > height:
        raise ValueError("Nagłówki tabeli nie tworzą jednego wiersza.")
    top = max(y + h for _, y, _, h, _ in columns)
    totals = [y for _, y, _, _, text in words if y > top and text.lower().strip("‘’'") == "summe"]
    article_edge = columns[3][0] + columns[3][2]
    if len(totals) != 1 or xs[4] - article_edge < height:
        raise ValueError("Nie znaleziono granic tabeli lub miejsca na oznaczenia.")
    return max(0, xs[0] - height), article_edge, xs[4], top, totals[0], height


def _blue_cross(image, box, scale):
    crop = image.crop(box)
    pixels = iter(crop.tobytes())
    blue = bytes(255 if b - r >= 15 and b - g >= 10 else 0 for r, g, b in zip(pixels, pixels, pixels))
    mask = Image.frombytes("L", crop.size, blue)
    bounds = mask.getbbox()
    if bounds is None or mask.histogram()[255] < scale:
        return False
    left, top, right, bottom = bounds
    width, height = right - left, bottom - top
    if not (scale <= width <= 4 * scale and scale <= height <= 4 * scale):
        raise ValueError("Niejednoznaczne niebieskie oznaczenie przy pozycji faktury.")
    ink = mask.crop(bounds)
    # Require ink near all four corners and the crossing itself.
    for x, y in ((.2, .2), (.8, .2), (.2, .8), (.8, .8), (.5, .5)):
        neighborhood = ink.crop((
            int((x - .18) * width), int((y - .18) * height),
            int((x + .18) * width) + 1, int((y + .18) * height) + 1,
        ))
        if neighborhood.getbbox() is None:
            raise ValueError("Niejednoznaczne niebieskie oznaczenie przy pozycji faktury.")
    return True


def _read_rows(image, executable, bounds):
    left, article_edge, _, top, bottom, scale = bounds
    metadata = image.crop((left, top, article_edge, bottom)).convert("L")
    words = _ocr(executable, metadata.resize((metadata.width * _SCALE, metadata.height * _SCALE)), 6)
    # A photographed row may slope slightly from the quantity to the article number.
    lines = []
    for word in sorted(words, key=lambda item: item[1] + item[3] / 2):
        center = word[1] + word[3] / 2
        if not lines or center - lines[-1][0] > scale * _SCALE * .7:
            lines.append((center, []))
        lines[-1][1].append(word)

    rows = []
    for center, line in lines:
        text = " ".join(word[4] for word in sorted(line))
        match = _ITEM.fullmatch(text)
        if not match or int(match[1]) != len(rows) + 1:
            raise ValueError("OCR nie potwierdził kolejności i ilości pozycji faktury.")
        rows.append((match[1], int(match[2]), top + round(center / _SCALE - scale)))
    return rows


def read_insect_screen_service_photo(path, *, tesseract="tesseract"):
    executable = shutil.which(tesseract)
    if not executable:
        raise ValueError("Nie znaleziono Tesseract.")
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
    bounds = _table_bounds(_ocr(executable, image, 11))
    _, article_edge, description_left, _, bottom, scale = bounds
    rows = _read_rows(image, executable, bounds)
    positions = []
    for index, (reference, quantity, start) in enumerate(rows):
        end = rows[index + 1][2] if index + 1 < len(rows) else bottom
        if not _blue_cross(image, (article_edge, start, description_left + scale, end), scale):
            continue
        crop = image.crop((description_left - scale // 2, start, image.width, end)).convert("L")
        description = " ".join(word[4] for word in _ocr(
            executable, crop.resize((crop.width * _SCALE, crop.height * _SCALE)), 6,
        ))
        sizes = _SIZE.findall(description)
        screens = _SCREEN.findall(description)
        if not re.search(r"\bFenster\b", description, re.IGNORECASE) or len(sizes) != 1 or len(screens) != 1:
            raise ValueError(f"Pozycja {reference}: sprawdź opis moskitiery i wymiary na fakturze.")
        width, height = map(int, sizes[0])
        positions.append({
            "position": reference,
            "quantity": quantity,
            "service": "replace_insect_screen_in_existing_box",
            "screen_type": "roller" if screens[0].lower() == "rollo" else None,
            "source_window_width_mm": width,
            "source_window_height_mm": height,
            "order_width_mm": None,
            "order_height_mm": None,
            "price": None,
            "status": "review",
            "reason": "Sprawdź kasetę i prowadnice, zmierz wkład oraz uzupełnij wycenę.",
        })
    if not positions:
        raise ValueError("Nie znaleziono potwierdzonych niebieskich krzyżyków przy pozycjach.")
    return {"status": "sales_review_required", "mode": "offline", "positions": positions}
