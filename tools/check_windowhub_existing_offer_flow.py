"""Test existing-offer lookup, position correction and replacement in local forms."""

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.windowhub_existing_offer_lab import ExistingOfferLab
from tools.check_windowhub_two_position_flow import run_headless as create_offer


def load_fixture():
    scenario = json.loads((ROOT / "examples/windowhub-existing-offer-correction.json").read_text(encoding="utf-8"))
    source = json.loads((ROOT / "examples/windowhub-two-position-flow.json").read_text(encoding="utf-8"))
    draft = json.loads(json.dumps(create_offer(source)))
    for reference, row in zip(("10.0", "20.0"), draft["positions"]):
        row["reference"] = reference
    offer = {
        "number": scenario["offer_number"], "revision": 1, "document": draft["document"],
        "positions": list(reversed(draft["positions"])),
    }
    other = deepcopy(offer)
    other["number"] = "OFR/TEST/2026/110"
    return scenario, [other, offer]


def verify_saved(report, original, scenario):
    expected = next(item for item in original if item["number"] == scenario["offer_number"])
    actual = report["offer"]
    if (
        actual["number"] != expected["number"] or actual["revision"] != expected["revision"] + 1
        or actual["document"] != expected["document"]
        or [row["reference"] for row in actual["positions"]] != [row["reference"] for row in expected["positions"]]
    ):
        raise ValueError("Weryfikacja numeru, wersji lub listy pozycji nie powiodła się.")
    for before, after in zip(expected["positions"], actual["positions"]):
        if before["reference"] == scenario["position_reference"]:
            if any(after[key] != value for key, value in scenario["changes"].items()):
                raise ValueError("Zapis nie potwierdził korekty pozycji.")
            if any(after[key] != before[key] for key in ("reference", "quantity", "color_inside", "color_outside")):
                raise ValueError("Zmieniły się pola poza zakresem korekty.")
            result = after["simulation"]
            if result["scene"]["opening"] != {"width": after["width_mm"], "height": after["height_mm"]}:
                raise ValueError("Odczyt konstrukcji nie potwierdził wymiarów.")
            spec = after["specification"]
            if after["kind"] == "single":
                expected = "LEFT" if spec["opening"] == "DKL" else "RIGHT"
                if result["direction"] != expected:
                    raise ValueError("Odczyt nie potwierdził kierunku skrzydła.")
            else:
                sides = (spec["active_side"],) if after["kind"] == "stulp" else ("left", "right")
                expected = {side: "LEFT" if spec[f"{side}_opening"] == "DKL" else "RIGHT" for side in sides}
                if result["final_directions"] != expected:
                    raise ValueError("Odczyt nie potwierdził kierunków skrzydeł.")
                if after["kind"] == "stulp" and result.get("active_side") != spec["active_side"]:
                    raise ValueError("Odczyt nie potwierdził skrzydła czynnego.")
        elif after != before:
            raise ValueError("Zmieniła się inna pozycja oferty.")


def run_headless(scenario, offers):
    flow = ExistingOfferLab(offers)
    flow.existing_offer()
    flow.load(scenario["offer_number"])
    flow.select_position(scenario["position_reference"])
    flow.correct(scenario["changes"])
    return flow.save()


def run_forms(scenario, offers):
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("NaviMind · korekta istniejącej oferty · test offline")
    root.geometry("1040x600")
    content = ttk.Frame(root, padding=20)
    content.pack(fill="both", expand=True)
    flow = ExistingOfferLab(offers)
    completed, failures = {}, []

    def button(label, callback, fill=lambda: None):
        def invoke():
            try:
                callback()
                show()
            except Exception as exc:
                failures.append(exc)
                root.quit()
        widget = ttk.Button(content, text=label, command=invoke)
        widget.pack(anchor="w", pady=12)
        def execute():
            try:
                fill()
                widget.invoke()
            except Exception as exc:
                failures.append(exc)
                root.quit()
        root.after(1100, execute)

    def entry(label, value=""):
        ttk.Label(content, text=label).pack(anchor="w")
        widget = ttk.Entry(content, width=45)
        widget.insert(0, str(value))
        widget.pack(anchor="w", pady=(2, 8))
        return widget

    def show():
        for widget in content.winfo_children():
            widget.destroy()
        ttk.Label(content, text={
            "start": "Program otwarty", "lookup": "Wyszukiwanie istniejącej oferty",
            "positions": "Pozycje wczytanej oferty", "edit": "Korekta wskazanej pozycji",
            "review": "Kontrola zmienionej konstrukcji", "saved": "Korekta gotowa",
        }[flow.stage], font=("Arial", 18, "bold")).pack(anchor="w", pady=(0, 15))
        ttk.Label(content, text="Lokalne formularze i dane fikcyjne").pack(anchor="w")
        if flow.stage == "start":
            button("Istniejąca oferta", flow.existing_offer)
        elif flow.stage == "lookup":
            number = entry("Numer oferty")
            button("Wczytaj ofertę", lambda: flow.load(number.get()),
                   lambda: number.insert(0, scenario["offer_number"]))
        elif flow.stage == "positions":
            ttk.Label(content, text=f"Oferta {flow.loaded['number']} · wersja {flow.loaded['revision']}").pack(anchor="w", pady=8)
            tree = ttk.Treeview(content, columns=("ref", "kind", "size", "qty"), show="headings", height=4)
            for key, label in (("ref", "Numer pozycji"), ("kind", "Konstrukcja"), ("size", "Wymiary mm"), ("qty", "Ilość")):
                tree.heading(key, text=label)
            for row in flow.loaded["positions"]:
                tree.insert("", "end", iid=row["reference"],
                            values=(row["reference"], row["kind"], f"{row['width_mm']} x {row['height_mm']}", row["quantity"]))
            tree.pack(fill="x")
            def select():
                matches = [item for item in tree.get_children() if tree.item(item, "values")[0] == scenario["position_reference"]]
                if len(matches) != 1:
                    raise ValueError("Brak jednoznacznej pozycji na liście.")
                tree.selection_set(matches[0])
            def edit():
                selected = tree.selection()
                if len(selected) != 1:
                    raise ValueError("Zaznacz jedną pozycję.")
                flow.select_position(tree.item(selected[0], "values")[0])
            button("Edytuj pozycję", edit, select)
        elif flow.stage == "edit":
            ttk.Label(content, text=f"Pozycja {flow.reference}").pack(anchor="w", pady=8)
            fields = {key: entry(label, flow.current[key]) for key, label in (
                ("width_mm", "Szerokość mm"), ("height_mm", "Wysokość mm"),
            )}
            kind = ttk.Combobox(content, values=("single", "double_fixed", "stulp"), state="readonly")
            kind.set(flow.current["kind"])
            kind.pack(anchor="w", pady=8)
            specification = entry("Parametry konstrukcji w scenariuszu testowym", json.dumps(flow.current["specification"], ensure_ascii=False))
            def fill():
                for key, widget in fields.items():
                    widget.delete(0, "end")
                    widget.insert(0, str(scenario["changes"][key]))
                kind.set(scenario["changes"]["kind"])
                specification.delete(0, "end")
                specification.insert(0, json.dumps(scenario["changes"]["specification"]))
            def build():
                flow.correct({
                    "width_mm": int(fields["width_mm"].get()), "height_mm": int(fields["height_mm"].get()),
                    "kind": kind.get(), "specification": json.loads(specification.get()),
                })
            button("Przebuduj okno", build, fill)
        elif flow.stage == "review":
            current = flow.current
            ttk.Label(content, text=f"Pozycja {flow.reference} · {current['width_mm']} x {current['height_mm']} mm").pack(anchor="w", pady=8)
            for step in current["simulation"]["trace"]:
                ttk.Label(content, text=step["stage"]).pack(anchor="w")
            button("Zapisz zmianę pozycji", lambda: completed.update(flow.save()))
        else:
            ttk.Label(content, text="Zastąpiono wskazaną pozycję · oferta do weryfikacji handlowca").pack(anchor="w", pady=12)
            root.after(1000, root.quit)

    try:
        show()
        root.mainloop()
        if failures:
            raise ValueError(str(failures[0]))
        if not completed:
            raise ValueError("Przerwano test przed zapisem korekty.")
        return completed
    finally:
        root.destroy()


def main(argv=None):
    from tkinter import TclError

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        scenario, offers = load_fixture()
        original = deepcopy(offers)
        report = run_headless(scenario, offers) if args.headless else run_forms(scenario, offers)
        verify_saved(report, original, scenario)
        if offers[0] != original[0]:
            raise ValueError("Zmieniła się inna oferta.")
        report["test_assumptions"] = scenario["test_assumptions"]
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        verify_saved(json.loads(args.output.read_text(encoding="utf-8")), original, scenario)
        print(f"OFFER={report['offer']['number']} REVISION={report['offer']['revision']}")
        changed = next(row for row in report["offer"]["positions"] if row["reference"] == report["changed_position"])
        print(f"POSITION={changed['reference']} SIZE={changed['width_mm']}x{changed['height_mm']} "
              f"ACTIVE={changed['simulation']['active_side'].upper()} MULLION={changed['specification']['mullion']}")
        print(f"OTHER_POSITIONS=preserved POSITIONS={len(report['offer']['positions'])}")
        print("WH_EXISTING_OFFER_FLOW_RESULT=verified MODE=" + ("headless" if args.headless else "forms"))
        return 0
    except (OSError, ValueError, TclError) as exc:
        print(f"WH_EXISTING_OFFER_FLOW_RESULT=review\n{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
