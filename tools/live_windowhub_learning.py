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
        print("
[STOP] Demonstracja przerwana.")
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

    print()
    print("[DONE] Learned workflow:")
    print(json.dumps(workflow.to_payload(), ensure_ascii=False, indent=2))
    print()
    print(f"[SAVED] {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
