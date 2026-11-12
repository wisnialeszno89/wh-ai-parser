"""Run an offline two-position offer through local forms and verified simulators."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.windowhub_offer_workflow_lab import OfferWorkflowLab
from tools.check_windowhub_builder_sequence import main as check_archive
from tools.visual_offer_lab import DOCUMENT_FIELDS


def verify_saved(report, scenario):
    if report["document"] != scenario["document"] or len(report["positions"]) != len(scenario["positions"]):
        raise ValueError("Odczyt oferty nie potwierdził klienta lub liczby pozycji.")
    for observed, requested in zip(report["positions"], scenario["positions"]):
        for key, value in requested.items():
            if observed.get(key) != value:
                raise ValueError(f"Zapis pozycji różni się od zlecenia w polu {key}.")
        if observed["simulation"]["scene"]["opening"] != {
            "width": requested["width_mm"], "height": requested["height_mm"],
        }:
            raise ValueError("Zapis konstrukcji nie potwierdził wymiarów.")


def run_headless(scenario):
    workflow = OfferWorkflowLab()
    workflow.new_offer()
    workflow.confirm_document(scenario["document"])
    for index, row in enumerate(scenario["positions"]):
        if index:
            workflow.next_position()
        workflow.select_window(row["kind"])
        workflow.set_dimensions(row["quantity"], row["width_mm"], row["height_mm"])
        workflow.set_color(row["color_inside"], row["color_outside"])
        workflow.build(row["specification"])
        workflow.add_position()
    return workflow.save()


def run_forms(scenario, keep_open):
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("NaviMind · dwie pozycje · test offline")
    root.geometry("940x710")
    content = ttk.Frame(root, padding=20)
    content.pack(fill="both", expand=True)
    workflow = OfferWorkflowLab()
    completed = {}
    failure = []

    def screen(title):
        for widget in content.winfo_children():
            widget.destroy()
        ttk.Label(content, text=title, font=("Arial", 18, "bold")).pack(anchor="w", pady=(0, 12))
        ttk.Label(content, text="Scenariusz testowy · sterowanie formularzami lokalnymi").pack(anchor="w", pady=(0, 12))

    def advance(action):
        try:
            action()
            show_stage()
        except Exception as exc:
            failure.append(exc)
            root.quit()

    def button(label, action, fill=lambda: None):
        widget = ttk.Button(content, text=label, command=lambda: advance(action))
        widget.pack(anchor="w", pady=12)
        def execute():
            try:
                fill()
                widget.invoke()
            except Exception as exc:
                failure.append(exc)
                root.quit()
        root.after(900, execute)

    def entry(label):
        ttk.Label(content, text=label).pack(anchor="w")
        widget = ttk.Entry(content, width=35)
        widget.pack(anchor="w", pady=(2, 8))
        return widget

    def choice(label, options):
        ttk.Label(content, text=label).pack(anchor="w")
        widget = ttk.Combobox(content, values=options, state="readonly", width=35)
        widget.pack(anchor="w", pady=(2, 8))
        return widget

    def show_stage():
        stage = workflow.stage
        index = len(workflow.positions)
        row = scenario["positions"][index] if index < len(scenario["positions"]) else None
        screen({
            "start": "Program otwarty", "document": "Właściwości dokumentu",
            "item_type": "Dodawanie nowej pozycji", "dimensions": "Wymiary okna",
            "color": "Kolory profili", "builder": "Budowa okna",
            "position_review": "Kontrola konstrukcji", "offer": "Pozycje oferty",
            "saved": "Gotowa oferta testowa",
        }[stage])
        if stage == "start":
            button("Nowa oferta", workflow.new_offer)
        elif stage == "document":
            query = entry("Wyszukaj klienta")
            clients = tk.Listbox(content, height=2, exportselection=False)
            clients.pack(anchor="w")
            checks = {}
            for key, label, _ in DOCUMENT_FIELDS:
                variable = tk.BooleanVar()
                checks[key] = variable
                ttk.Checkbutton(content, text=label, variable=variable).pack(anchor="w")
            def fill_document():
                query.insert(0, scenario["document"]["customer"])
                for name in ("Top Trans S.A.", "Top Trans"):
                    if query.get().casefold() in name.casefold():
                        clients.insert("end", name)
                names = clients.get(0, "end")
                clients.selection_set(names.index(scenario["document"]["customer"]))
                for key, variable in checks.items():
                    variable.set(scenario["document"][key])
            def confirm():
                selected = clients.curselection()
                if len(selected) != 1:
                    raise ValueError("Wybierz jednego klienta.")
                workflow.confirm_document({
                    "customer": clients.get(selected[0]), "confirmed": True,
                    **{key: variable.get() for key, variable in checks.items()},
                })
            button("OK", confirm, fill_document)
        elif stage == "item_type":
            kind = choice("Okno", ("single", "double_fixed"))
            button("Dalej", lambda: workflow.select_window(kind.get()), lambda: kind.set(row["kind"]))
        elif stage == "dimensions":
            fields = {key: entry(label) for key, label in [
                ("quantity", "Ilość"), ("width_mm", "Szerokość w mm"), ("height_mm", "Wysokość w mm"),
            ]}
            def fill_dimensions():
                for key, widget in fields.items():
                    widget.insert(0, str(row[key]))
            button("Dalej", lambda: workflow.set_dimensions(*(int(widget.get()) for widget in fields.values())), fill_dimensions)
        elif stage == "color":
            inside = choice("Kolor wewnętrzny", ("biały", "antracyt"))
            outside = choice("Kolor zewnętrzny", ("biały", "antracyt"))
            def fill_color():
                inside.set(row["color_inside"])
                outside.set(row["color_outside"])
            button("Przejdź do budowy", lambda: workflow.set_color(inside.get(), outside.get()), fill_color)
        elif stage == "builder":
            spec = row["specification"]
            fields = {key: entry(key) for key in spec}
            def fill_specification():
                for key, widget in fields.items():
                    widget.insert(0, str(spec[key]))
            def build():
                numeric = {"glazing_panes", "split_from_left_mm"}
                workflow.build({key: int(widget.get()) if key in numeric else widget.get() for key, widget in fields.items()})
            button("Buduj", build, fill_specification)
        elif stage == "position_review":
            current = workflow.current
            result = current["simulation"]
            ttk.Label(content, text=f"{current['width_mm']} × {current['height_mm']} mm · {current['color_inside']} / {current['color_outside']}").pack(anchor="w")
            ttk.Label(content, text=" → ".join(step["stage"] for step in result["trace"]), wraplength=850).pack(anchor="w", pady=10)
            canvas = tk.Canvas(content, width=420, height=280, background="white")
            canvas.pack(anchor="w")
            canvas.create_rectangle(20, 20, 400, 260, width=5)
            sides = result.get("final_directions", {"center": result.get("direction")})
            if len(sides) == 2:
                canvas.create_line(210, 20, 210, 260, width=5)
            for side, direction in sides.items():
                left, right = (20, 210) if side == "left" else (210, 400) if side == "right" else (20, 400)
                handle = right - 14 if direction == "LEFT" else left + 14
                canvas.create_line(handle, 130, handle, 155, width=4)
            button("Dodaj pozycję do oferty", workflow.add_position)
        elif stage == "offer":
            for number, position in enumerate(workflow.positions, 1):
                ttk.Label(content, text=f"{number}. {position['kind']} · {position['quantity']} szt. · {position['width_mm']} × {position['height_mm']} mm").pack(anchor="w")
            button("Następna pozycja", workflow.next_position) if index < len(scenario["positions"]) else button("Zapisz szkic", lambda: completed.update(workflow.save()))
        else:
            ttk.Label(content, text="Pozycje gotowe · zamknij okno, aby zapisać szkic do weryfikacji handlowca").pack(anchor="w")
            if not keep_open:
                root.after(500, root.quit)

    try:
        show_stage()
        root.mainloop()
        if failure:
            raise ValueError(str(failure[0]))
        if not completed:
            raise ValueError("Zamknięto formularz przed ukończeniem testu.")
        return completed
    finally:
        root.destroy()


def main(argv=None):
    from tkinter import TclError

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--keep-open", action="store_true")
    args = parser.parse_args(argv)
    try:
        if check_archive() != 0:
            raise ValueError("Archiwum nie potwierdziło sekwencji budowy.")
        scenario = json.loads((ROOT / "examples/windowhub-two-position-flow.json").read_text(encoding="utf-8"))
        report = run_headless(scenario) if args.headless else run_forms(scenario, args.keep_open)
        verify_saved(report, scenario)
        report["test_assumptions"] = scenario["test_assumptions"]
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        verify_saved(json.loads(args.output.read_text(encoding="utf-8")), scenario)
        print("DOCUMENT=Top Trans PREFERENCES=verified")
        for number, row in enumerate(report["positions"], 1):
            print(f"POSITION={number} STATUS=simulated SIZE={row['width_mm']}x{row['height_mm']} "
                  f"COLOR_INSIDE={row['color_inside']} COLOR_OUTSIDE={row['color_outside']}")
        print("WH_TWO_POSITION_FLOW_RESULT=verified POSITIONS=2 MODE=" + ("headless" if args.headless else "forms"))
        return 0
    except (OSError, ValueError, TclError) as exc:
        print(f"WH_TWO_POSITION_FLOW_RESULT=review\n{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
