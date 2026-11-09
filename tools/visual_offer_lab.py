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
DOCUMENT_TITLE = "NaviMind Document Properties Lab"
DOCUMENT_STATE_FILE = Path(tempfile.gettempdir()) / "navimind-document-properties-lab.json"
DOCUMENT_CUSTOMER = "Top Trans"
DOCUMENT_FIELDS = (
    ("construction", "Bez ceny konstrukcji", False),
    ("installation", "Bez ceny montażu", True),
    ("removal", "Bez ceny demontażu", True),
    ("finishing", "Bez ceny wykończenia", True),
)
DOCUMENT_GOAL = (
    "Pole wyszukiwania klienta ma początkowy fokus. Wyszukaj i wybierz dokładnie Top Trans z listy. "
    "Odznacz Bez ceny konstrukcji. Zaznacz Bez ceny montażu, Bez ceny demontażu i Bez ceny wykończenia. "
    "Korzystaj z odczytu stanu. Jeśli zaznaczony wiersz to Top Trans, nie wybieraj klienta ponownie. "
    "Pracuj w pełnym widoku formularza. Kliknij OK i zakończ po wyświetleniu potwierdzenia. Nie zamykaj okna."
)
GOAL = (
    "Zapisz testowy szkic oferty dla klienta Klient Demo, z montażem. "
    "Dodaj 2 sztuki okna o szerokości 1500 mm i wysokości 1400 mm. "
    "Zakończ po wyświetleniu zapisanego szkicu. Nie zamykaj okna."
)


def save_state(path, nonce, draft, *, title=TITLE, document_ready=False, document_snapshot=None):
    state = dict(title=title, pid=os.getpid(), nonce=nonce, draft=draft)
    if title == DOCUMENT_TITLE:
        state["document_ready"] = document_ready
        state["document_snapshot"] = document_snapshot
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


def read_lab_state(path, nonce, pid, title):
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(state, dict):
        return None
    if (state.get("title"), state.get("nonce"), state.get("pid")) != (title, nonce, pid):
        return None
    return state


def read_lab_draft(path, nonce, pid, title):
    state = read_lab_state(path, nonce, pid, title)
    draft = state.get("draft") if state else None
    return draft if isinstance(draft, dict) else None


def document_observer(path, nonce, pid):
    def observe():
        state = read_lab_state(path, nonce, pid, DOCUMENT_TITLE)
        if state is None:
            return None
        confirmed = isinstance(state.get("draft"), dict)
        snapshot = state["draft"] if confirmed else state.get("document_snapshot")
        if not isinstance(snapshot, dict) or any(type(snapshot.get(key)) is not bool for key, _, _ in DOCUMENT_FIELDS):
            return None
        customer = snapshot.get("customer")
        if customer not in (None, DOCUMENT_CUSTOMER, "Top Trans S.A.", "Klient Testowy"):
            return None
        prices = "; ".join(f"{label}: {'zaznaczone' if snapshot[key] else 'odznaczone'}"
                           for key, label, _ in DOCUMENT_FIELDS)
        return (
            f"Stan formularza testowego. Zaznaczony klient: {customer or 'brak'}. "
            f"{prices}. Formularz po OK: {'tak' if confirmed else 'nie'}."
        )

    return observe


def document_start_ready(state):
    return (
        state.get("title") == DOCUMENT_TITLE
        and state.get("document_ready") is True
        and "draft" in state
        and state["draft"] is None
    )


def document_verifier(path, nonce, pid):
    def verify():
        draft = read_lab_draft(path, nonce, pid, DOCUMENT_TITLE)
        return (
            draft is not None
            and draft.get("customer") == DOCUMENT_CUSTOMER
            and draft.get("confirmed") is True
            and all(draft.get(key) is checked for key, _, checked in DOCUMENT_FIELDS)
        )

    return verify


def offer_verifier(path, nonce, pid):
    def verify():
        draft = read_lab_draft(path, nonce, pid, TITLE)
        if draft is None:
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
    parser.add_argument("--state-file", type=Path)
    parser.add_argument("--document-only", action="store_true", help="Open the Top Trans document properties scenario")
    args = parser.parse_args(argv)
    nonce = secrets.token_hex(16)
    title = DOCUMENT_TITLE if args.document_only else TITLE
    state_path = args.state_file or (DOCUMENT_STATE_FILE if args.document_only else STATE_FILE)

    root = tk.Tk()
    root.title(title)
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
        save_state(state_path, nonce, None, title=title)
        show("Właściwości dokumentu" if args.document_only else "1 z 3 · Właściwości dokumentu")
        query = tk.StringVar(value="" if args.document_only else "AKlient Demo")
        installation = tk.BooleanVar(value=False)
        customers = (
            ("Top Trans S.A.", DOCUMENT_CUSTOMER, "Klient Testowy")
            if args.document_only else (CUSTOMER, "Klient Testowy")
        )
        options = {}
        ttk.Label(content, text="Wyszukaj istniejącego klienta").pack(anchor="w")
        search_entry = ttk.Entry(content, textvariable=query, width=34)
        search_entry.pack(anchor="w", pady=(4, 6))
        results = tk.Listbox(content, height=2, width=34, exportselection=False)
        results.pack(anchor="w", pady=(0, 10))

        document_ready = False

        def write_document_state():
            selected = results.curselection()
            snapshot = {key: variable.get() for key, variable in options.items()}
            snapshot["customer"] = results.get(selected[0]) if selected else None
            save_state(state_path, nonce, None, title=title,
                       document_ready=document_ready, document_snapshot=snapshot)

        def mark_document_changed(*_):
            nonlocal document_ready
            document_ready = False
            write_document_state()

        def filter_customers(*_):
            results.delete(0, "end")
            term = query.get().strip().casefold()
            if term:
                for customer in customers:
                    if term in customer.casefold():
                        results.insert("end", customer)
            message.set("" if results.size() else "Brak wyników. Zmień wyszukiwaną nazwę.")
            if args.document_only:
                mark_document_changed()

        def next_step():
            selected = results.curselection()
            if not selected:
                message.set("Wybierz klienta z listy wyników.")
                return
            customer = results.get(selected[0])
            if args.document_only:
                draft = {key: variable.get() for key, variable in options.items()}
                draft.update(customer=customer, confirmed=True)
                save_state(state_path, nonce, draft, title=title)
                show("Właściwości dokumentu zatwierdzone")
                ttk.Label(content, text=f"Klient: {customer}").pack(anchor="w")
                for key, label, _ in DOCUMENT_FIELDS:
                    ttk.Label(content, text=f"{label}: {'TAK' if draft[key] else 'NIE'}").pack(anchor="w")
                print("DOCUMENT_LAB_RESULT=" + (
                    "confirmed" if document_verifier(state_path, nonce, os.getpid())() else "preferences_mismatch"
                ), flush=True)
            else:
                dimensions(customer, installation.get())

        if args.document_only:
            for key, label, expected in DOCUMENT_FIELDS:
                options[key] = tk.BooleanVar(value=not expected)
                ttk.Checkbutton(content, text=label, variable=options[key], command=mark_document_changed).pack(anchor="w")
        else:
            ttk.Checkbutton(content, text="Montaż", variable=installation).pack(anchor="w", pady=(0, 8))
        ttk.Button(content, text="OK" if args.document_only else "Dalej", command=next_step).pack(anchor="w", pady=(8, 0))
        message = tk.StringVar()
        ttk.Label(content, textvariable=message).pack(anchor="w", pady=8)
        query.trace_add("write", filter_customers)
        filter_customers()
        if args.document_only:
            results.bind("<<ListboxSelect>>", mark_document_changed)
            root.after_idle(search_entry.focus_set)
            document_ready = True
            write_document_state()

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
            save_state(state_path, nonce, draft)
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

    if args.document_only:
        new_offer()
    else:
        save_state(state_path, nonce, None)
        show("Laboratorium WindowHub")
        ttk.Button(content, text="Nowa oferta", command=new_offer).pack(anchor="w")
    print(f"VISUAL_LAB_STATE_FILE={state_path}", flush=True)
    root.mainloop()


if __name__ == "__main__":
    main()
