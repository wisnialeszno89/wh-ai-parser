from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_learning_controller import (
    WindowHubLearningController,
)


def _print_workflow_summary(workflow) -> None:
    payload = workflow.to_payload()
    steps = payload.get("steps", [])

    print()
    print("=" * 80)
    print("NAUKA ZAKOŃCZONA — SKRÓT")
    print("=" * 80)
    print(f"Workflow : {payload.get('name')}")
    print(f"Trigger  : {payload.get('trigger')}")
    print(f"Aplikacja: {payload.get('application')}")
    print(f"Liczba kroków: {len(steps)}")
    print()

    if not steps:
        print("BRAK ZAREJESTROWANYCH KROKÓW.")
        return

    for step in steps:
        action = step.get("action", {})
        before = step.get("before") or {}
        after = step.get("after") or {}

        action_name = action.get("name") or "?"
        target = action.get("target")
        value = action.get("value")

        print(
            f"KROK {step.get('index', '?')}: "
            f"{action_name}"
            + (f" -> {target}" if target else "")
            + (f" = {value}" if value else "")
        )

        before_title = before.get("window_title")
        after_title = after.get("window_title")
        before_doc = before.get("active_document")
        after_doc = after.get("active_document")

        if before_title != after_title:
            print(f"  okno: {before_title!r} -> {after_title!r}")
        if before_doc != after_doc:
            print(f"  dokument: {before_doc!r} -> {after_doc!r}")

        before_count = len(before.get("elements", []))
        after_count = len(after.get("elements", []))
        print(f"  elementy semantyczne: {before_count} -> {after_count}")

        before_labels = {
            e.get("semantic_name")
            for e in before.get("elements", [])
            if e.get("semantic_name")
        }
        after_labels = {
            e.get("semantic_name")
            for e in after.get("elements", [])
            if e.get("semantic_name")
        }
        added = sorted(after_labels - before_labels)
        removed = sorted(before_labels - after_labels)

        if added:
            print("  pojawiły się: " + ", ".join(added[:8]))
            if len(added) > 8:
                print(f"  ... +{len(added) - 8} kolejnych")
        if removed:
            print("  zniknęły: " + ", ".join(removed[:8]))
            if len(removed) > 8:
                print(f"  ... -{len(removed) - 8} kolejnych")

        print()

    print("=" * 80)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Teach the agent a WindowHub workflow by demonstrating it with the mouse."
        )
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Human-readable workflow name.",
    )
    parser.add_argument(
        "--trigger",
        required=True,
        help="Phrase that should later trigger the learned workflow.",
    )
    parser.add_argument(
        "--workflow-id",
        default=None,
        help="Optional stable workflow id.",
    )
    parser.add_argument(
        "--output",
        default="outputs/learned_windowhub_workflow.json",
        help="Where to write the learned workflow JSON.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only a concise summary; full workflow JSON is still saved.",
    )

    args = parser.parse_args()

    workflow_id = (
        args.workflow_id
        or f"windowhub-learn-{uuid4().hex}"
    )

    controller = WindowHubLearningController()

    print("=" * 120)
    print("WINDOWHUB — TRYB NAUKI")
    print("=" * 120)
    print()
    print("WindowHub zostanie przejęty przez agenta tylko po to,")
    print("aby ustawić prawidłowe źródło obserwacji.")
    print()
    print("Po komunikacie START wykonuj normalnie swoją pracę myszą w WindowHub.")
    print("Kliknięcia poza WindowHub są ignorowane.")
    print("Nie wpisuj haseł ani innych sekretów — pierwsza wersja nie nagrywa klawiatury.")
    print()

    try:
        controller.start(
            workflow_id=workflow_id,
            name=args.name,
            trigger=args.trigger,
        )
    except Exception as exc:
        print(f"[LEARN ERROR] {exc}")
        return 1

    print("[START] Agent obserwuje WindowHub. Naciśnij ENTER po zakończeniu demonstracji.")
    try:
        input()
    except KeyboardInterrupt:
        print("\n[STOP] Demonstracja przerwana.")
        controller.discard()
        return 130

    try:
        workflow = controller.finish()
    except Exception as exc:
        print(f"[LEARN ERROR] {exc}")
        controller.discard()
        return 1

    output_path = Path(args.output)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output_path.write_text(
        json.dumps(
            workflow.to_payload(),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    if args.summary_only:
        _print_workflow_summary(workflow)
    else:
        print()
        print("[DONE] Learned workflow:")
        print(json.dumps(workflow.to_payload(), ensure_ascii=False, indent=2))

    print()
    print(f"[SAVED] {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
