"""Synthetic offer wizard for the existing visual agent pilot."""

import argparse
import json
import os
import secrets
import tempfile
from dataclasses import dataclass
from pathlib import Path

TITLE = "NaviMind Visual Offer Lab"
STATE_FILE = Path(tempfile.gettempdir()) / "navimind-visual-offer-lab.json"
CUSTOMER = "Klient Demo"
DOCUMENT_TITLE = "NaviMind Document Properties Lab"
DOCUMENT_STATE_FILE = Path(tempfile.gettempdir()) / "navimind-document-properties-lab.json"
ORDER_TITLE = "NaviMind Order Lab"
ORDER_STATE_FILE = Path(tempfile.gettempdir()) / "navimind-order-lab.json"
DOCUMENT_CUSTOMER = "Top Trans"
WINDOW_FIELDS = (
    ("quantity", "Ilość sztuk", 2),
    ("width", "Szerokość (mm)", 1500),
    ("height", "Wysokość (mm)", 1400),
)
DOCUMENT_FIELDS = (
    ("construction", "Bez ceny konstrukcji", False),
    ("installation", "Bez ceny montażu", True),
    ("removal", "Bez ceny demontażu", True),
    ("finishing", "Bez ceny wykończenia", True),
)
DOCUMENT_TASK = (
    "Pole wyszukiwania klienta ma początkowy fokus. Wyszukaj i wybierz dokładnie Top Trans z listy. "
    "Odznacz Bez ceny konstrukcji. Zaznacz Bez ceny montażu, Bez ceny demontażu i Bez ceny wykończenia. "
    "Korzystaj z odczytu stanu i podanych punktów kliknięcia w pikselach bieżącego obrazu. "
    "Jeśli zaznaczony wiersz to Top Trans, nie wybieraj klienta ponownie. "
    "Pracuj w pełnym widoku formularza. Kliknij OK. "
)
DOCUMENT_GOAL = DOCUMENT_TASK + "Zakończ po wyświetleniu potwierdzenia. Nie zamykaj okna."
DEFAULT_ORDER_CASE = "top-trans"


@dataclass(frozen=True)
class OrderCase:
    customer: str
    similar_customer: str
    price_states: tuple[bool, bool, bool, bool]
    dimensions: tuple[int, int, int]

    def goal(self):
        preferences = " ".join(
            f"{'Zaznacz' if checked else 'Odznacz'} {label}."
            for (_, label, _), checked in zip(DOCUMENT_FIELDS, self.price_states)
        )
        quantity, width, height = self.dimensions
        return (
            f"Pole wyszukiwania klienta ma początkowy fokus. Wyszukaj i wybierz dokładnie {self.customer} z listy. "
            f"{preferences} Korzystaj z odczytu stanu i punktów kliknięcia. "
            "Gdy właściwy klient jest zaznaczony, przejdź do ustawień cen i zatwierdź OK. "
            f"Po OK uzupełnij pozycję: {quantity} szt., szerokość {width} mm, wysokość {height} mm. "
            "Wpisanie zastępuje wartość w aktywnym polu liczbowym. "
            "Sprawdź Podsumowanie, zapisz szkic i zakończ. Nie zamykaj okna."
        )


ORDER_CASES = {
    DEFAULT_ORDER_CASE: OrderCase(
        DOCUMENT_CUSTOMER, "Top Trans S.A.",
        tuple(checked for _, _, checked in DOCUMENT_FIELDS),
        tuple(expected for _, _, expected in WINDOW_FIELDS),
    ),
    "baupartner": OrderCase("Baupartner Nord", "Baupartner Nord GmbH", (True, False, False, True), (3, 1230, 1780)),
}

GOAL = (
    "Zapisz testowy szkic oferty dla klienta Klient Demo, z montażem. "
    "Dodaj 2 sztuki okna o szerokości 1500 mm i wysokości 1400 mm. "
    "Zakończ po wyświetleniu zapisanego szkicu. Nie zamykaj okna."
)


def save_state(path, nonce, draft, *, title=TITLE, document_ready=False, document_snapshot=None, order_case=DEFAULT_ORDER_CASE):
    state = dict(title=title, pid=os.getpid(), nonce=nonce, draft=draft)
    if title in {DOCUMENT_TITLE, ORDER_TITLE}:
        state["document_ready"] = document_ready
        state["document_snapshot"] = document_snapshot
    if title == ORDER_TITLE:
        state["order_case"] = order_case
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


def document_image_points(snapshot, frame):
    """Convert Tk client-relative points to pixels of the current screenshot."""
    if frame is None or frame.token is None:
        return {}
    size = snapshot.get("client_size")
    points = snapshot.get("points")
    if not isinstance(size, list) or len(size) != 2 or any(type(n) is not int or n <= 0 for n in size):
        return {}
    if not isinstance(points, dict):
        return {}
    left, top, right, bottom = frame.token.window_box
    vx, vy, vr, vb = frame.token.view_box
    if vr <= vx or vb <= vy:
        return {}
    result = {}
    for label, point in points.items():
        if not isinstance(point, list) or len(point) != 2 or any(type(n) is not int for n in point):
            continue
        x = point[0] * (right - left) / size[0]
        y = point[1] * (bottom - top) / size[1]
        if vx <= x < vr and vy <= y < vb:
            result[label] = (int((x - vx) * frame.image.width / (vr - vx)),
                             int((y - vy) * frame.image.height / (vb - vy)))
    return result


def order_numeric_focus(path, nonce, pid):
    def focused():
        state = read_lab_state(path, nonce, pid, ORDER_TITLE)
        snapshot = state.get("document_snapshot") if state else None
        return (
            isinstance(snapshot, dict)
            and snapshot.get("stage") == "pozycja"
            and snapshot.get("focus") in {label for _, label, _ in WINDOW_FIELDS}
        )

    return focused


def order_position_action(path, nonce, pid, case):
    """Choose one lab position action from the current session's widget state."""
    order = ORDER_CASES[case]

    def action(kind, reason, **fields):
        return dict(kind=kind, reason=reason, **(
            dict.fromkeys(("x", "y", "width", "height", "text", "key", "direction", "amount")) | fields
        ))

    def choose(frame):
        state = read_lab_state(path, nonce, pid, ORDER_TITLE)
        if state is None or state.get("order_case") != case:
            return action("ask_user", "Stan formularza nie należy do tej sesji zlecenia.")
        if isinstance(state.get("draft"), dict):
            return action("done", "Szkic zapisany. Weryfikator sprawdzi komplet danych.")
        snapshot = state.get("document_snapshot")
        if not isinstance(snapshot, dict) or snapshot.get("stage") not in {"pozycja", "podsumowanie"}:
            return None

        points = document_image_points(snapshot, frame)

        def click(key, reason):
            if key not in points:
                return action("ask_user", f"Brak widocznego punktu dla kontrolki {key}.")
            x, y = points[key]
            return action("click", reason, x=x, y=y)

        if snapshot["stage"] == "podsumowanie":
            if matches_window(snapshot, order):
                return click("save", "Wymiary w podsumowaniu są zgodne. Zapisz szkic.")
            return click("edit", "Wymiary w podsumowaniu wymagają poprawy.")

        for (key, label, _), expected in zip(WINDOW_FIELDS, order.dimensions):
            if str(snapshot.get(key, "")) != str(expected):
                if snapshot.get("focus") == label:
                    return action("type_text", f"Ustaw wartość pola {label}.", text=str(expected))
                return click(key, f"Ustaw fokus w polu {label}.")
        return click("review", "Wszystkie pola są zgodne. Przejdź do podsumowania.")

    return choose


def position_observation(snapshot, frame, order):
    points = document_image_points(snapshot, frame)
    stage = snapshot["stage"]
    fields = "; ".join(
        f"{label} = {str(snapshot.get(key, ''))[:24] or 'puste'}"
        + (f" {points[key]}" if key in points else "")
        for key, label, _ in WINDOW_FIELDS
    )
    actions = "; ".join(
        f"{label} {points[key]}" for key, label in
        (("review", "Podsumowanie"), ("save", "Zapisz szkic"), ("edit", "Popraw pozycję"))
        if key in points
    )
    focus = snapshot.get("focus")
    next_step = ""
    if stage == "pozycja":
        next_field = next(((label, expected) for (key, label, _), expected in zip(WINDOW_FIELDS, order.dimensions)
                           if str(snapshot.get(key, "")) != str(expected)), None)
        if next_field is None:
            next_step = " Wszystkie wartości poprawne. Kliknij Podsumowanie."
        else:
            label, expected = next_field
            verb = "Wpisz" if focus == label else "Ustaw fokus i wpisz"
            next_step = f" {verb} {expected} w polu {label}. Poprawnych pól nie zmieniaj."
    return (
        f"Właściwości {order.customer} zatwierdzone. Etap: {stage}. {fields}. "
        f"Pole z fokusem: {focus or 'brak'}. Punkty x,y: {actions or 'brak'}.{next_step}"
    )


def document_observer(path, nonce, pid, *, title=DOCUMENT_TITLE):
    def observe(frame=None):
        state = read_lab_state(path, nonce, pid, title)
        if state is None:
            return None
        confirmed = isinstance(state.get("draft"), dict)
        snapshot = state["draft"] if confirmed else state.get("document_snapshot")
        order = None
        if title == ORDER_TITLE:
            case = state.get("order_case")
            order = ORDER_CASES.get(case) if isinstance(case, str) else None
            if order is None:
                return None
            if confirmed:
                return "Szkic zapisany. Sprawdź, czy zadanie zostało wykonane."
            if isinstance(snapshot, dict) and snapshot.get("stage") in {"pozycja", "podsumowanie"}:
                return position_observation(snapshot, frame, order)
        if not isinstance(snapshot, dict) or any(type(snapshot.get(key)) is not bool for key, _, _ in DOCUMENT_FIELDS):
            return None
        customer = snapshot.get("customer")
        customer_names = (
            (order.similar_customer, order.customer, "Klient Testowy")
            if order else ("Top Trans S.A.", DOCUMENT_CUSTOMER, "Klient Testowy")
        )
        if customer is not None and customer not in customer_names:
            return None
        points = document_image_points(snapshot, frame)
        def point(label):
            return f" {points[label]}" if label in points else ""

        prices = "; ".join(
            f"{label}: {'zaznaczone' if snapshot[key] else 'odznaczone'}{point(key)}"
            for key, label, _ in DOCUMENT_FIELDS
        )
        rows = ", ".join(f"{name}{point(name)}" for name in customer_names if name in points)
        return (
            f"Stan formularza testowego. Zaznaczony klient: {customer or 'brak'}. "
            f"{prices}. Formularz po OK: {'tak' if confirmed else 'nie'}. "
            + (f"Punkty x,y: pole szukania{point('search')}; wyniki: {rows or 'brak'}; OK{point('ok')}." if points else "")
        ).strip()

    return observe


def document_start_ready(state):
    return (
        state.get("title") in {DOCUMENT_TITLE, ORDER_TITLE}
        and state.get("document_ready") is True
        and "draft" in state
        and state["draft"] is None
    )


def matches_document(draft, order=None):
    customer = order.customer if order else DOCUMENT_CUSTOMER
    price_states = order.price_states if order else tuple(checked for _, _, checked in DOCUMENT_FIELDS)
    return (
        isinstance(draft, dict)
        and draft.get("customer") == customer
        and draft.get("confirmed") is True
        and all(draft.get(key) is checked for (key, _, _), checked in zip(DOCUMENT_FIELDS, price_states))
    )


def document_verifier(path, nonce, pid):
    return lambda: matches_document(read_lab_draft(path, nonce, pid, DOCUMENT_TITLE))


def matches_window(draft, order=None):
    dimensions = order.dimensions if order else tuple(expected for _, _, expected in WINDOW_FIELDS)
    return all(type(draft.get(key)) is int and draft[key] == expected
               for (key, _, _), expected in zip(WINDOW_FIELDS, dimensions))


def order_verifier(path, nonce, pid, case=DEFAULT_ORDER_CASE):
    order = ORDER_CASES[case]

    def verify():
        state = read_lab_state(path, nonce, pid, ORDER_TITLE)
        if state is None or state.get("order_case") != case:
            return False
        draft = state.get("draft")
        return (
            isinstance(draft, dict)
            and matches_document(draft.get("document"), order)
            and matches_window(draft, order)
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
            and matches_window(draft)
        )

    return verify


def main(argv=None):
    import tkinter as tk
    from tkinter import ttk

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-file", type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--document-only", action="store_true", help="Open the Top Trans document properties scenario")
    modes.add_argument("--order", action="store_true", help="Run an order properties and window draft scenario")
    parser.add_argument("--order-case", choices=ORDER_CASES)
    args = parser.parse_args(argv)
    if args.order_case and not args.order:
        parser.error("--order-case requires --order")
    case = args.order_case or DEFAULT_ORDER_CASE
    order = ORDER_CASES[case] if args.order else None
    nonce = secrets.token_hex(16)
    document_mode = args.document_only or args.order
    title, default_path = TITLE, STATE_FILE
    if args.order:
        title, default_path = ORDER_TITLE, ORDER_STATE_FILE
    elif args.document_only:
        title, default_path = DOCUMENT_TITLE, DOCUMENT_STATE_FILE
    state_path = args.state_file or default_path

    root = tk.Tk()
    root.title(title)
    root.geometry("740x480+100+100")
    root.minsize(620, 440)
    content = ttk.Frame(root, padding=24)
    content.pack(fill="both", expand=True)

    def write_state(draft, **kwargs):
        save_state(state_path, nonce, draft, title=title, order_case=case, **kwargs)

    def show(title):
        content.unbind("<Configure>")
        for widget in content.winfo_children():
            widget.destroy()
        ttk.Label(content, text=title, font=("Arial", 18, "bold")).pack(anchor="w", pady=(0, 16))
        ttk.Label(content, text="Laboratorium ofert · dane fikcyjne").pack(anchor="w", pady=(0, 12))

    def relative(widget, x, y):
        return [widget.winfo_rootx() - root.winfo_rootx() + x,
                widget.winfo_rooty() - root.winfo_rooty() + y]

    def widget_points(widgets):
        return {
            key: relative(widget, widget.winfo_width() // 2, widget.winfo_height() // 2)
            for key, widget in widgets.items() if widget.winfo_ismapped()
        }

    def observe_stage_widgets(stage, widgets, values):
        def publish():
            if not all(widget.winfo_exists() for widget in widgets.values()):
                return
            snapshot = values()
            snapshot.update(stage=stage, points=widget_points(widgets),
                            client_size=[root.winfo_width(), root.winfo_height()])
            write_state(None, document_snapshot=snapshot)

        root.update_idletasks()
        publish()
        content.bind("<Configure>", lambda _: publish())
        return publish

    def new_offer():
        write_state(None)
        show("Właściwości dokumentu" if document_mode else "1 z 3 · Właściwości dokumentu")
        query = tk.StringVar(value="" if document_mode else "AKlient Demo")
        installation = tk.BooleanVar(value=False)
        customers = (
            (order.similar_customer, order.customer, "Klient Testowy")
            if order else ("Top Trans S.A.", DOCUMENT_CUSTOMER, "Klient Testowy")
            if document_mode else (CUSTOMER, "Klient Testowy")
        )
        options = {}
        price_widgets = {}
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
            widgets = {"search": search_entry, "ok": ok_button, **price_widgets}
            points = widget_points(widgets)
            for index, name in enumerate(results.get(0, "end")):
                bounds = results.bbox(index)
                if bounds:
                    x, y, width, height = bounds
                    points[name] = relative(results, x + width // 2, y + height // 2)
            snapshot["points"] = points
            snapshot["client_size"] = [root.winfo_width(), root.winfo_height()]
            write_state(None, document_ready=document_ready, document_snapshot=snapshot)

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
            if document_mode:
                mark_document_changed()

        def next_step():
            selected = results.curselection()
            if not selected:
                message.set("Wybierz klienta z listy wyników.")
                return
            customer = results.get(selected[0])
            if document_mode:
                draft = {key: variable.get() for key, variable in options.items()}
                draft.update(customer=customer, confirmed=True)
                if args.order:
                    if not matches_document(draft, order):
                        message.set("Sprawdź klienta i zaznaczenia pól przed przejściem dalej.")
                        return
                    dimensions(customer, None, document=draft)
                    return
                write_state(draft)
                show("Właściwości dokumentu zatwierdzone")
                ttk.Label(content, text=f"Klient: {customer}").pack(anchor="w")
                for key, label, _ in DOCUMENT_FIELDS:
                    ttk.Label(content, text=f"{label}: {'TAK' if draft[key] else 'NIE'}").pack(anchor="w")
                print("DOCUMENT_LAB_RESULT=" + (
                    "confirmed" if document_verifier(state_path, nonce, os.getpid())() else "preferences_mismatch"
                ), flush=True)
            else:
                dimensions(customer, installation.get())

        if document_mode:
            for index, (key, label, expected) in enumerate(DOCUMENT_FIELDS):
                checked = order.price_states[index] if order else expected
                options[key] = tk.BooleanVar(value=not checked)
                price_widgets[key] = ttk.Checkbutton(content, text=label, variable=options[key], command=mark_document_changed)
                price_widgets[key].pack(anchor="w")
        else:
            ttk.Checkbutton(content, text="Montaż", variable=installation).pack(anchor="w", pady=(0, 8))
        ok_button = ttk.Button(content, text="OK" if document_mode else "Dalej", command=next_step)
        ok_button.pack(anchor="w", pady=(8, 0))
        message = tk.StringVar()
        ttk.Label(content, textvariable=message).pack(anchor="w", pady=8)
        query.trace_add("write", filter_customers)
        filter_customers()
        if document_mode:
            results.bind("<<ListboxSelect>>", mark_document_changed)
            root.after_idle(search_entry.focus_set)
            root.update_idletasks()

            def refresh_positions(event):
                if event.widget is root and results.winfo_exists():
                    write_document_state()

            root.bind("<Configure>", refresh_positions, add="+")
            document_ready = True
            write_document_state()

    def dimensions(customer, installation, *, document=None, initial=None):
        show("2 z 3 · Dodawanie pozycji okiennej")
        header = f"Klient: {customer}"
        if document is None:
            header += f" · Montaż: {'TAK' if installation else 'NIE'}"
        ttk.Label(content, text=header).pack(anchor="w", pady=(0, 8))
        entries = {}
        variables = {}
        for key, label, _ in WINDOW_FIELDS:
            ttk.Label(content, text=label).pack(anchor="w")
            variables[key] = tk.StringVar(value=str(initial[key]) if initial else "")
            entry = ttk.Entry(content, width=18, textvariable=variables[key])
            entry.pack(anchor="w", pady=(2, 8))
            entries[key] = entry

        def review():
            try:
                quantity, width, height = read_dimensions(value.get() for value in variables.values())
            except ValueError as exc:
                message.set(str(exc))
                return
            draft = dict(customer=customer, installation=installation, quantity=quantity, width=width, height=height)
            if document is not None:
                draft["document"] = document
            summary(draft)

        review_button = ttk.Button(content, text="Podsumowanie", command=review)
        review_button.pack(anchor="w")
        ttk.Button(content, text="Wróć do wyboru klienta", command=new_offer).pack(anchor="w", pady=(6, 0))
        message = tk.StringVar()
        ttk.Label(content, textvariable=message).pack(anchor="w", pady=8)

        if document is not None:
            def current_values():
                active = root.focus_get()
                focus = next((label for key, label, _ in WINDOW_FIELDS if entries[key] == active), None)
                return dict(focus=focus, **{key: variable.get() for key, variable in variables.items()})

            entries["quantity"].focus_set()
            publish = observe_stage_widgets("pozycja", {**entries, "review": review_button}, current_values)
            def select_value(event):
                event.widget.selection_range(0, "end")
                return "break"

            for key, entry in entries.items():
                variables[key].trace_add("write", lambda *_: publish())
                entry.bind("<FocusIn>", lambda _: publish())
                entry.bind("<FocusOut>", lambda _: publish())
                entry.bind("<Control-a>", select_value)

    def summary(draft):
        show("3 z 3 · Podsumowanie oferty")
        ttk.Label(content, text=f"Klient: {draft['customer']}").pack(anchor="w")
        document = draft.get("document")
        if document is None:
            ttk.Label(content, text=f"Montaż: {'TAK' if draft['installation'] else 'NIE'}").pack(anchor="w")
        ttk.Label(
            content,
            text=f"Okno · {draft['quantity']} szt. · {draft['width']} × {draft['height']} mm (szer. × wys.)",
        ).pack(anchor="w", pady=(0, 16))

        def save():
            if document is not None and not matches_window(draft, order):
                message.set("Ilość lub wymiary nie zgadzają się ze zleceniem. Kliknij Popraw pozycję.")
                return
            content.unbind("<Configure>")
            write_state(draft)
            message.set("Szkic zapisany w laboratorium.")
            save_button.state(["disabled"])
            edit_button.state(["disabled"])
            if document is not None:
                result = "verified" if order_verifier(state_path, nonce, os.getpid(), case)() else "mismatch"
                print(f"ORDER_LAB_RESULT={result}", flush=True)

        save_button = ttk.Button(content, text="Zapisz szkic", command=save)
        save_button.pack(anchor="w")
        edit_button = ttk.Button(
            content, text="Popraw pozycję",
            command=lambda: dimensions(draft["customer"], draft["installation"], document=document,
                                       initial=draft if document is not None else None),
        )
        edit_button.pack(anchor="w", pady=(6, 0))
        message = tk.StringVar()
        ttk.Label(content, textvariable=message).pack(anchor="w", pady=8)
        if document is not None:
            observe_stage_widgets("podsumowanie", {"save": save_button, "edit": edit_button},
                                  lambda: {key: draft[key] for key, _, _ in WINDOW_FIELDS})

    if document_mode:
        new_offer()
    else:
        save_state(state_path, nonce, None)
        show("Laboratorium WindowHub")
        ttk.Button(content, text="Nowa oferta", command=new_offer).pack(anchor="w")
    print(f"VISUAL_LAB_STATE_FILE={state_path}", flush=True)
    root.mainloop()


if __name__ == "__main__":
    main()
