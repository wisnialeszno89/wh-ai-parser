"""Read-only semantic inspection of a blank/new WindowHub offer form.

The tool requires the user to place the new offer form in the foreground.
It lists only UI Automation control metadata and never prints field values.
It does not click, type, save, or change application data.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Sequence

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.agent.environment.windows_desktop_environment_adapter import (
    WindowsDesktopEnvironmentAdapter,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.windows_ui_automation_provider import (
    WindowsUIAutomationProvider,
)


FORM_CONTROL_TYPES = frozenset(
    {
        "button",
        "edit",
        "checkbox",
        "combobox",
        "hyperlink",
        "listitem",
        "menuitem",
        "radiobutton",
        "splitbutton",
        "tabitem",
        "treeitem",
        "table",
    }
)


def _configure_console_output() -> None:
    """Keep Windows console output from failing on unsupported characters."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(errors="backslashreplace")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read UI Automation metadata for the foreground WindowHub form. "
            "Field contents are never printed."
        )
    )
    parser.add_argument(
        "--process",
        default="Okna.exe",
        help="Expected foreground process basename (default: Okna.exe)",
    )
    parser.add_argument(
        "--max-controls",
        type=int,
        default=250,
        help="Maximum number of semantic controls to print (1-500)",
    )
    return parser.parse_args()


def summarize_controls(
    elements: Sequence[ScreenElement],
    *,
    max_controls: int = 250,
) -> tuple[dict[str, object], ...]:
    """Project controls to safe metadata; never return or print their values."""
    if (
        isinstance(max_controls, bool)
        or not isinstance(max_controls, int)
        or not 1 <= max_controls <= 500
    ):
        raise ValueError("new_offer_form_control_limit_invalid")

    records: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()

    for element in elements:
        if not isinstance(element, ScreenElement):
            continue

        control_type = (
            element.kind.strip().casefold()
            if isinstance(element.kind, str)
            else ""
        )
        label = (
            element.label.strip()
            if isinstance(element.label, str)
            else ""
        )
        if (
            control_type not in FORM_CONTROL_TYPES
            or not label
        ):
            continue

        metadata = element.metadata or {}
        automation_id = metadata.get("automation_id")
        class_name = metadata.get("uia_class_name")
        runtime_id = metadata.get("uia_runtime_id")
        identity = (
            control_type,
            label.casefold(),
            automation_id if isinstance(automation_id, str) else "",
            runtime_id if isinstance(runtime_id, str) else "",
        )
        if identity in seen:
            continue
        seen.add(identity)

        current_value = metadata.get("current_value")
        value_present = (
            current_value is not None
            and current_value != ""
            and current_value != ()
        )
        records.append(
            {
                "label": label[:160],
                "control_type": control_type,
                "automation_id": (
                    automation_id[:120]
                    if isinstance(automation_id, str)
                    else ""
                ),
                "class_name": (
                    class_name[:120]
                    if isinstance(class_name, str)
                    else ""
                ),
                "enabled": metadata.get("uia_enabled") is True,
                "focused": (
                    metadata.get("uia_focused")
                    if isinstance(metadata.get("uia_focused"), bool)
                    else None
                ),
                # Only a boolean is exposed. The actual value is discarded.
                "value_present": bool(value_present),
                "label_source": (
                    str(metadata.get("semantic_label_source", ""))[:60]
                ),
            }
        )
        if len(records) >= max_controls:
            break

    return tuple(records)


def main() -> int:
    _configure_console_output()

    if os.name != "nt":
        print("This inspection tool requires Windows.")
        return 2

    args = _parse_args()
    if not 1 <= args.max_controls <= 500:
        print("--max-controls must be between 1 and 500.")
        return 2

    try:
        observation = WindowsDesktopEnvironmentAdapter().observe()
    except Exception as exc:
        print(f"Could not observe the foreground desktop: {type(exc).__name__}")
        return 2

    expected_process = args.process.strip().casefold()
    active_process = (
        observation.state.active_application.strip().casefold()
        if isinstance(observation.state.active_application, str)
        else ""
    )
    if not expected_process or active_process != expected_process:
        print("Wrong foreground application; nothing was inspected.")
        print(f"Expected process: {args.process}")
        print(f"Foreground process: {observation.state.active_application}")
        print("Bring a blank/new WindowHub offer form to the foreground and retry.")
        return 2

    print("=== WINDOWHUB NEW OFFER FORM (READ ONLY) ===")
    print(f"Foreground window: {observation.state.active_window_title or '<NO TITLE>'}")
    print("Field contents: HIDDEN")
    print("No mouse, keyboard, save, or form actions will be performed.")

    try:
        elements = WindowsUIAutomationProvider().perceive(observation)
    except Exception as exc:
        print(f"UI Automation perception failed: {type(exc).__name__}")
        return 2

    records = summarize_controls(
        elements,
        max_controls=args.max_controls,
    )
    if not records:
        print("No labeled semantic form controls were exposed by UI Automation.")
        print("The form remains unchanged.")
        return 1

    print(f"Semantic controls found: {len(records)}")
    print("\nNO. | TYPE | LABEL | AUTOMATION_ID | ENABLED | FOCUSED | VALUE_PRESENT | LABEL_SOURCE")
    print("-" * 150)

    for index, record in enumerate(records, start=1):
        print(
            f"{index:03d} | "
            f"{record['control_type']} | "
            f"{record['label']} | "
            f"{record['automation_id'] or '-'} | "
            f"{'yes' if record['enabled'] else 'no'} | "
            f"{record['focused'] if record['focused'] is not None else '-'} | "
            f"{'yes' if record['value_present'] else 'no'} | "
            f"{record['label_source'] or '-'}"
        )

    print("\nInspection complete. No form values were displayed or changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
