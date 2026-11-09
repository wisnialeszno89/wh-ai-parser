"""Synthetic offer wizard for the existing visual agent pilot."""

import argparse
import json
import os
import secrets
import tempfile
from pathlib import Path

TITLE = "NaviMind Visual Offer Lab"
STATE_FILE = Path(tempfile.gettempdir()) / "navimind-visual-offer-lab.json"
CUSTOMER = "Klient Demo"
GOAL = (
    "Zapisz testowy szkic oferty dla klienta Klient Demo, z montażem. "
    "Dodaj 2 sztuki okna o szerokości 1500 mm i wysokości 1400 mm. "
    "Zakończ po wyświetleniu zapisanego szkicu. Nie zamykaj okna."
)


def save_state(path, nonce, draft):
    state = dict(title=TITLE, pid=os.getpid(), nonce=nonce, draft=draft)
    temporary = path.with_name(f".{path.name}.{nonce}.tmp")
    temporary.write_text(json.dumps(state), encoding="utf-8")
    os.replace(temporary, path)


def read_dimensions(entries):
    values = tuple(entry.strip() for entry in entries)
    if any(not value.isascii() or not value.isdecimal() or len(value) > 4 for value in values):
        raise ValueError("Wpisz dodatnie liczby całkowite (maksymalnie 4 cyfry).")
    numbers = tuple(map(int, values))
    if not all(numbers):
        raise ValueError("Wartości muszą być większe od zera.")
    return numbers


def offer_verifier(path, nonce, pid):
    def verify():
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        if not isinstance(state, dict):
            return False
        if (state.get("title"), state.get("nonce"), state.get("pid")) != (TITLE, nonce, pid):
            return False
        draft = state.get("draft")
        if not isinstance(draft, dict):
            return False
        return (
            draft.get("customer") == CUSTOMER
            and draft.get("installation") is True
            and all(
                type(draft.get(key)) is int and draft[key] == expected
                for key, expected in (("quantity", 2), ("width", 1500), ("height", 1400))
            )
        )

    return verify


def main(argv=None):
    import tkinter as tk
    from tkinter import ttk

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-file", type=Path, default=STATE_FILE)
    args = parser.parse_args(argv)
    nonce = secrets.token_hex(16)

    root = tk.Tk()
    root.title(TITLE)
    root.geometry("740x480+100+100")
    root.minsize(620, 440)
    content = ttk.Frame(root, padding=24)
    content.pack(fill="both", expand=True)

    def show(title):
        for widget in content.winfo_children():
            widget.destroy()
        ttk.Label(content, text=title, font=("Arial", 18, "bold")).pack(anchor="w", pady=(0, 16))
        ttk.Label(content, text="Laboratorium ofert · dane fikcyjne").pack(anchor="w", pady=(0, 12))

    def new_offer():
        save_state(args.state_file, nonce, None)
        show("1 z 3 · Właściwości dokumentu")
        query = tk.StringVar(value="AKlient Demo")
        installation = tk.BooleanVar(value=False)
        ttk.Label(content, text="Wyszukaj istniejącego klienta").pack(anchor="w")
        ttk.Entry(content, textvariable=query, width=34).pack(anchor="w", pady=(4, 6))
        results = tk.Listbox(content, height=2, width=34, exportselection=False)
        results.pack(anchor="w", pady=(0, 10))

        def filter_customers(*_):
            results.delete(0, "end")
            term = query.get().strip().casefold()
            if term:
                for customer in (CUSTOMER, "Klient Testowy"):
                    if term in customer.casefold():
                        results.insert("end", customer)
            message.set("" if results.size() else "Brak wyników. Zmień wyszukiwaną nazwę.")

        def next_step():
            selected = results.curselection()
            if not selected:
                message.set("Wybierz klienta z listy wyników.")
                return
            dimensions(results.get(selected[0]), installation.get())

        ttk.Checkbutton(content, text="Montaż", variable=installation).pack(anchor="w", pady=(0, 8))
        ttk.Button(content, text="Dalej", command=next_step).pack(anchor="w")
        message = tk.StringVar()
        ttk.Label(content, textvariable=message).pack(anchor="w", pady=8)
        query.trace_add("write", filter_customers)
        filter_customers()

    def dimensions(customer, installation):
        show("2 z 3 · Dodawanie pozycji okiennej")
        ttk.Label(content, text=f"Klient: {customer} · Montaż: {'TAK' if installation else 'NIE'}").pack(anchor="w", pady=(0, 8))
        fields = []
        for label in ("Ilość sztuk", "Szerokość (mm)", "Wysokość (mm)"):
            ttk.Label(content, text=label).pack(anchor="w")
            entry = ttk.Entry(content, width=18)
            entry.pack(anchor="w", pady=(2, 8))
            fields.append(entry)

        def review():
            try:
                quantity, width, height = read_dimensions(entry.get() for entry in fields)
            except ValueError as exc:
                message.set(str(exc))
                return
            summary(dict(customer=customer, installation=installation, quantity=quantity, width=width, height=height))

        ttk.Button(content, text="Podsumowanie", command=review).pack(anchor="w")
        ttk.Button(content, text="Wróć do wyboru klienta", command=new_offer).pack(anchor="w", pady=(6, 0))
        message = tk.StringVar()
        ttk.Label(content, textvariable=message).pack(anchor="w", pady=8)

    def summary(draft):
        show("3 z 3 · Podsumowanie oferty")
        ttk.Label(content, text=f"Klient: {draft['customer']}").pack(anchor="w")
        ttk.Label(content, text=f"Montaż: {'TAK' if draft['installation'] else 'NIE'}").pack(anchor="w")
        ttk.Label(
            content,
            text=f"Okno · {draft['quantity']} szt. · {draft['width']} × {draft['height']} mm (szer. × wys.)",
        ).pack(anchor="w", pady=(0, 16))

        def save():
            save_state(args.state_file, nonce, draft)
            message.set("Szkic zapisany w laboratorium.")
            save_button.state(["disabled"])
            edit_button.state(["disabled"])

        save_button = ttk.Button(content, text="Zapisz szkic", command=save)
        save_button.pack(anchor="w")
        edit_button = ttk.Button(
            content, text="Popraw pozycję", command=lambda: dimensions(draft["customer"], draft["installation"])
        )
        edit_button.pack(anchor="w", pady=(6, 0))
        message = tk.StringVar()
        ttk.Label(content, textvariable=message).pack(anchor="w", pady=8)

    save_state(args.state_file, nonce, None)
    show("Laboratorium WindowHub")
    ttk.Button(content, text="Nowa oferta", command=new_offer).pack(anchor="w")
    print(f"VISUAL_LAB_STATE_FILE={args.state_file}", flush=True)
    root.mainloop()


if __name__ == "__main__":
    main()
