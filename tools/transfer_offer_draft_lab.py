"""Transfer an OCR offer draft into an isolated Tk offer form."""

import argparse
import json
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.intake.german_offer_photo import read_german_offer_photo_file
from app.agent.offers.offer_draft_routing import CatalogStatus, DraftPosition, route_draft_positions

FIELDS = {
    "reference": "Pozycja", "execution": "Tryb", "description": "Opis",
    "quantity": "Sztuki", "width_mm": "Szerokość [mm]", "height_mm": "Wysokość [mm]",
    "system": "System", "construction": "Konstrukcja", "opening": "Otwieranie",
    "header_code": "Kod nagłówka", "strip_material": "Materiał listwy", "strip_side": "Strona listwy",
    "strip_sides": "Liczba stron listwy", "strip_size_mm": "Wymiar listwy [mm]",
    "note_code": "Kod uwagi", "price": "Cena katalogowa (symulacja)", "discount_percent": "Rabat [%]",
}
POSITION_FIELDS = ("quantity", "width_mm", "height_mm", "system", "construction", "opening", "header_code", "note_code")
STRIP_FIELDS = ("material", "side", "sides", "size_mm")
NUMERIC_FIELDS = {"quantity", "width_mm", "height_mm", "strip_sides"}
LAB_CATALOG_PRICE = "1000.00"
OFFER_STATUS = "sales_review_required"


def parse_requested_discount(value):
    if value is None:
        return None
    value = value.strip().replace(",", ".")
    if not re.fullmatch(r"[0-9]{1,3}(?:\.[0-9]{1,2})?", value) or Decimal(value) > 100:
        raise ValueError("Rabat musi być liczbą od 0 do 100 z maksymalnie dwoma miejscami po przecinku.")
    return format(Decimal(value).normalize(), "f")


def plan_lab_transfer(draft, unavailable):
    if not isinstance(draft, dict) or draft.get("status") != "technical_draft":
        raise ValueError("Oczekiwano szkicu technicznego OCR.")
    rows = draft.get("positions")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Szkic musi zawierać aktywne pozycje.")

    positions = []
    references = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Nieprawidłowa pozycja szkicu.")
        ref = row.get("position")
        strip = row.get("cover_strip")
        if not isinstance(ref, str) or not ref.strip() or ref in references or not isinstance(strip, dict):
            raise ValueError(f"Brak unikalnego numeru lub danych listwy: {ref!r}.")
        references.add(ref)
        config = {key: row.get(key) for key in POSITION_FIELDS}
        config.update({f"strip_{key}": strip.get(key) for key in STRIP_FIELDS})
        for key, value in config.items():
            if key in NUMERIC_FIELDS:
                valid = type(value) is int and value > 0
            else:
                valid = isinstance(value, str) and bool(value.strip())
            if not valid:
                raise ValueError(f"Pozycja {ref}: nieprawidłowe pole {key}.")

        description = (
            f"{row['system']} · {row['construction']} · {row['opening']} · "
            f"{row['quantity']} szt. · {row['width_mm']} × {row['height_mm']} mm · "
            f"listwa {strip['material']}, {strip['side']}, {strip['sides']} str., {strip['size_mm']} mm · "
            f"{row['header_code']} · {row['note_code']}"
        )
        supported = (
            ref not in unavailable
            and (row["system"], row["construction"]) == ("Zirkon", "F004 DK-Fenster")
            and row["opening"] in {"DKL", "DKR"}
        )
        status = CatalogStatus.SUPPORTED if supported else CatalogStatus.UNSUPPORTED
        positions.append(DraftPosition(ref, description, status, config))
    if unavailable - references:
        raise ValueError("Symulowana niedostępność wskazuje pozycję spoza szkicu.")
    return route_draft_positions(positions)


def form_values(position):
    values = {**position, **position.get("configuration", {})}
    return tuple(str(values[key]) if values.get(key) is not None else "" for key in FIELDS)


def serialize_form_rows(rows):
    saved = []
    for values in rows:
        row = {
            key: int(value) if key in NUMERIC_FIELDS else value
            for key, value in zip(FIELDS, values) if value
        }
        row.setdefault("price", None)
        saved.append(row)
    return saved


def transfer_in_form(root, positions, output, keep_open=False, *, requested_discount=None):
    from tkinter import ttk

    root.title("NaviMind · laboratorium przenoszenia oferty")
    form = ttk.Frame(root, padding=12)
    form.pack(fill="both", expand=True)
    entries = []
    for index, label in enumerate(FIELDS.values()):
        row, column = divmod(index, 3)
        ttk.Label(form, text=label).grid(row=row * 2, column=column, sticky="w")
        entry = ttk.Entry(form, width=34)
        entry.grid(row=row * 2 + 1, column=column, sticky="ew", padx=(0, 6))
        entries.append(entry)
    price_index = tuple(FIELDS).index("price")
    discount_index = tuple(FIELDS).index("discount_percent")
    execution_index = tuple(FIELDS).index("execution")
    entries[price_index].state(["readonly"])

    tree = ttk.Treeview(root, columns=tuple(FIELDS), show="headings", height=7,
                        displaycolumns=("reference", "execution", "description", "price", "discount_percent"))
    for column, width in (("reference", 65), ("execution", 85), ("description", 690),
                          ("price", 190), ("discount_percent", 80)):
        tree.heading(column, text=FIELDS[column])
        tree.column(column, width=width)
    tree.pack(fill="both", expand=True, padx=12)

    def readback():
        return [tuple(map(str, tree.item(row, "values"))) for row in tree.get_children()]

    def add_position():
        values = [entry.get() for entry in entries]
        if values[execution_index] == "configure":
            values[price_index] = LAB_CATALOG_PRICE
        tree.insert("", "end", values=values)
        entries[discount_index].delete(0, "end")

    saved_ok = False
    save_error = None

    def save():
        nonlocal saved_ok, save_error
        try:
            rows = serialize_form_rows(readback())
            output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            saved_ok = True
        except (OSError, ValueError) as exc:
            save_error = exc

    add_button = ttk.Button(root, text="Dodaj pozycję", command=add_position)
    save_button = ttk.Button(root, text="Zapisz szkic", command=save)
    add_button.pack(side="left", padx=12, pady=12)
    save_button.pack(side="left", pady=12)
    root.update_idletasks()

    expected = []
    for position in positions:
        values = list(form_values(position))
        if position["execution"] == "configure":
            values[price_index] = LAB_CATALOG_PRICE
            if requested_discount is not None:
                values[discount_index] = requested_discount
        expected.append(tuple(values))
        for index, (entry, value) in enumerate(zip(entries, values)):
            if index == price_index or (index == discount_index and not value):
                continue
            entry.delete(0, "end")
            entry.insert(0, value)
        add_button.invoke()
    if readback() != expected:
        raise ValueError("Odczyt formularza różni się od planu. Przerwano zapis.")
    save_button.invoke()
    if not saved_ok:
        raise ValueError(f"Formularz nie zapisał szkicu: {save_error}")
    saved = json.loads(output.read_text(encoding="utf-8"))
    if saved != serialize_form_rows(expected):
        raise ValueError("Zapisany szkic różni się od planu.")
    add_button.state(["disabled"])
    save_button.state(["disabled"])
    ttk.Label(root, text="Szkic zapisany · cała oferta do weryfikacji handlowca").pack(side="left", padx=12)
    print("DRAFT_TRANSFER_RESULT=verified", flush=True)
    print(f"DRAFT_OFFER_STATUS={OFFER_STATUS}", flush=True)
    print("DRAFT_TRANSFER_ORDER=" + ",".join(row["reference"] for row in saved), flush=True)
    print("DRAFT_TRANSFER_MANUAL=" + ",".join(row["reference"] for row in saved if row["execution"] == "manual"), flush=True)
    if keep_open:
        root.protocol("WM_DELETE_WINDOW", root.quit)
        root.mainloop()


def main(argv=None):
    import tkinter as tk

    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--draft-file", type=Path)
    source.add_argument("--photo", type=Path, help="Read a German offer photo with Tesseract before opening the form.")
    parser.add_argument("--tesseract", default="tesseract", help="Tesseract executable for --photo.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--simulate-unsupported", action="append", default=[], metavar="POSITION")
    parser.add_argument("--discount-percent", help="Apply an explicitly requested discount to catalog items.")
    parser.add_argument("--keep-open", action="store_true", help="Leave the verified lab form open for inspection.")
    args = parser.parse_args(argv)
    try:
        input_file = args.photo or args.draft_file
        if input_file.resolve() == args.output.resolve():
            raise ValueError("Plik wyjściowy musi być inny niż źródłowy.")
        requested_discount = parse_requested_discount(args.discount_percent)
        if args.photo:
            draft = read_german_offer_photo_file(args.photo, tesseract=args.tesseract)
            print("PHOTO_OFFER_RESULT=technical_draft", flush=True)
        else:
            draft = json.loads(args.draft_file.read_text(encoding="utf-8-sig"))
        positions = plan_lab_transfer(draft, set(args.simulate_unsupported))
        root = tk.Tk()
        try:
            transfer_in_form(root, positions, args.output, args.keep_open, requested_discount=requested_discount)
        finally:
            root.destroy()
    except (OSError, ValueError, subprocess.SubprocessError, tk.TclError) as exc:
        print(f"DRAFT_TRANSFER_RESULT=review\n{exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
