"""Live WindowHub v2 smoke: inspect UIA grid structure, never table contents.

The script may open the known customer lookup popup, but only to expose its
DataGrid structure. It does not read cells, headers, names, or values, select
a record, invoke NaviMind, plan an action, or save an offer.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOOKUP_AUTOMATION_ID = "IDC_ZAMAWIAJACY"
LOOKUP_CLASS_NAME = "lookupedit"
GRID_AUTOMATION_ID = "PART_GridControl"
GRID_CONTROL_TYPE = "datagrid"


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _runtime_id(value: object) -> str | None:
    if isinstance(value, (tuple, list)) and value:
        return "-".join(str(part) for part in value)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _window_area(window: object) -> int:
    try:
        rect = window.rectangle()
        return max(0, int(rect.width())) * max(0, int(rect.height()))
    except Exception:
        return 0


def _foreground_relation_matches(
    *,
    foreground_handle: int,
    foreground_root_handle: int,
    foreground_root_owner_handle: int,
    windowhub_handle: int,
) -> bool:
    """Accept the main WindowHub window or one of its owned popup windows."""
    return (
        windowhub_handle > 0
        and (
            foreground_handle == windowhub_handle
            or foreground_root_handle == windowhub_handle
            or foreground_root_owner_handle == windowhub_handle
        )
    )


def _foreground_windowhub_relation(windowhub_handle: int) -> dict[str, bool]:
    """Read foreground HWND ancestry using pointer-sized Win32 types."""
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    get_foreground = user32.GetForegroundWindow
    get_foreground.argtypes = ()
    get_foreground.restype = ctypes.wintypes.HWND

    get_ancestor = user32.GetAncestor
    get_ancestor.argtypes = (
        ctypes.wintypes.HWND,
        ctypes.wintypes.UINT,
    )
    get_ancestor.restype = ctypes.wintypes.HWND

    foreground_raw = get_foreground()
    foreground_handle = int(foreground_raw or 0)

    foreground_root_handle = 0
    foreground_root_owner_handle = 0
    if foreground_handle > 0:
        foreground_hwnd = ctypes.wintypes.HWND(foreground_handle)
        foreground_root_handle = int(
            get_ancestor(foreground_hwnd, 2) or 0
        )  # GA_ROOT
        foreground_root_owner_handle = int(
            get_ancestor(foreground_hwnd, 3) or 0
        )  # GA_ROOTOWNER

    belongs = _foreground_relation_matches(
        foreground_handle=foreground_handle,
        foreground_root_handle=foreground_root_handle,
        foreground_root_owner_handle=foreground_root_owner_handle,
        windowhub_handle=windowhub_handle,
    )
    return {
        "foreground_matches_windowhub": (
            foreground_handle == windowhub_handle
        ),
        "foreground_root_matches_windowhub": (
            foreground_root_handle == windowhub_handle
        ),
        "foreground_root_owner_matches_windowhub": (
            foreground_root_owner_handle == windowhub_handle
        ),
        "belongs_to_windowhub": belongs,
    }


def _windowhub_window(desktop):
    candidates = []
    for window in desktop.windows():
        try:
            title = _text(window.window_text())
        except Exception:
            continue
        if title.casefold().startswith("okna -"):
            candidates.append((window, title))

    if not candidates:
        raise RuntimeError("windowhub_window_not_found")

    return max(candidates, key=lambda pair: _window_area(pair[0]))


def _descendants(window):
    try:
        return tuple(window.descendants())
    except Exception as exc:
        raise RuntimeError(
            f"windowhub_uia_descendants_failed:{type(exc).__name__}"
        ) from exc


def _element_info(item):
    try:
        return item.element_info
    except Exception:
        return None


def _find_grid(window):
    matches = []
    for item in _descendants(window):
        info = _element_info(item)
        if info is None:
            continue
        try:
            automation_id = _text(getattr(info, "automation_id", None))
            control_type = _text(getattr(info, "control_type", None)).casefold()
            visible = bool(getattr(info, "visible", True))
        except Exception:
            continue
        if (
            automation_id == GRID_AUTOMATION_ID
            and control_type == GRID_CONTROL_TYPE
            and visible
        ):
            matches.append(item)
    return matches


def _find_lookup(window):
    matches = []
    for item in _descendants(window):
        info = _element_info(item)
        if info is None:
            continue
        try:
            automation_id = _text(getattr(info, "automation_id", None))
            control_type = _text(getattr(info, "control_type", None)).casefold()
            class_name = _text(getattr(info, "class_name", None)).casefold()
            visible = bool(getattr(info, "visible", True))
            enabled = bool(getattr(info, "enabled", False))
        except Exception:
            continue
        if (
            automation_id == LOOKUP_AUTOMATION_ID
            and control_type == "button"
            and LOOKUP_CLASS_NAME in class_name
            and visible
            and enabled
        ):
            matches.append(item)
    return matches


def _open_lookup_popup(lookup) -> None:
    try:
        rect = lookup.rectangle()
        width = max(1, int(rect.width()))
        height = max(1, int(rect.height()))
        # Click only the right-hand drop-down affordance of the verified
        # LookUpEdit control, never a row or a table cell.
        x = max(1, width - min(12, max(1, width // 4)))
        y = max(1, height // 2)
        lookup.click_input(coords=(x, y), button="left")
    except Exception as exc:
        raise RuntimeError(
            f"lookup_popup_open_failed:{type(exc).__name__}"
        ) from exc


def _close_lookup_popup(lookup) -> bool:
    try:
        lookup.type_keys("{ESC}", set_foreground=False)
        return True
    except Exception:
        return False


def main() -> int:
    if os.name != "nt":
        print("result: FAIL (requires Windows)", file=sys.stderr)
        return 2

    if os.environ.get("WH_REAL_WINDOWHUB", "").strip() == "1":
        print(
            "result: FAIL (WH_REAL_WINDOWHUB=1 is prohibited for this read-only smoke)",
            file=sys.stderr,
        )
        return 2

    # Set COM apartment preference before importing pywinauto/comtypes.
    sys.coinit_flags = 2

    opened_by_script = False
    lookup = None
    cleanup_ok = None

    try:
        from pywinauto import Desktop

        from app.agent.bridge.agent_task_v2_world_builder import (
            AgentTaskV2WorldBuilder,
        )
        from app.agent.bridge.agent_task_contract_v2 import (
            validate_agent_task_v2_payload,
            validate_agent_task_v2_response,
        )
        from app.agent.environment.environment_observation import (
            EnvironmentObservation,
        )
        from app.agent.environment.environment_state import EnvironmentState
        from app.agent.perception.screen_element import ScreenElement
        from app.agent.perception.interaction_capability import (
            InteractionCapability,
        )
        from app.agent.perception.screen_scene import ScreenScene
        from app.agent.perception.windowhub_ui_automation_provider import (
            WindowHubUIAutomationProvider,
        )
        from app.agent.runtime.read_only_observation_broker import (
            ReadOnlyObservationBroker,
        )
        from app.agent.runtime.windowhub_uia_grid_structure_reader import (
            WindowHubUIAGridStructureReader,
            windowhub_grid_structure_capability_spec,
        )

        desktop = Desktop(backend="uia")
        window, title = _windowhub_window(desktop)
        window_handle = int(window.handle)
        if window_handle <= 0:
            raise RuntimeError("windowhub_handle_invalid")

        # First inspect only semantic identity/visibility metadata. If the
        # popup grid is already visible, do not activate the parent window:
        # doing so could dismiss that popup. If no grid is open, safely bring
        # the main WindowHub window forward before opening the known lookup.
        grids = _find_grid(window)
        if len(grids) > 1:
            raise RuntimeError("multiple_matching_windowhub_grids")

        brought_to_foreground = False
        foreground_relation = _foreground_windowhub_relation(
            window_handle
        )
        if not foreground_relation["belongs_to_windowhub"]:
            if grids:
                raise RuntimeError(
                    "windowhub_grid_visible_but_not_foreground:"
                    "refusing_to_dismiss_an_already_open_popup"
                )

            try:
                if bool(window.is_minimized()):
                    window.restore()
                window.set_focus()
            except Exception as exc:
                raise RuntimeError(
                    f"windowhub_activation_failed:{type(exc).__name__}"
                ) from exc

            activation_deadline = time.monotonic() + 2.0
            while time.monotonic() < activation_deadline:
                time.sleep(0.1)
                foreground_relation = _foreground_windowhub_relation(
                    window_handle
                )
                if foreground_relation["belongs_to_windowhub"]:
                    brought_to_foreground = True
                    break

            if not foreground_relation["belongs_to_windowhub"]:
                raise RuntimeError(
                    "windowhub_activation_not_confirmed:"
                    "focus_WindowHub_manually_and_rerun"
                )
        else:
            brought_to_foreground = False

        if not grids:
            lookups = _find_lookup(window)
            if len(lookups) != 1:
                raise RuntimeError(
                    f"verified_lookup_control_count_invalid:{len(lookups)}"
                )
            lookup = lookups[0]
            _open_lookup_popup(lookup)
            opened_by_script = True

            # Poll only UIA identity/visibility metadata. No control values
            # or GridPattern cells are queried during this wait.
            deadline = time.monotonic() + 4.0
            while time.monotonic() < deadline:
                time.sleep(0.1)
                grids = _find_grid(window)
                if len(grids) > 1:
                    raise RuntimeError("multiple_matching_windowhub_grids")
                if len(grids) == 1:
                    break

        if len(grids) != 1:
            raise RuntimeError("windowhub_grid_not_found_after_popup_open")

        grid = grids[0]
        info = _element_info(grid)
        if info is None:
            raise RuntimeError("windowhub_grid_element_info_unavailable")

        # Read only structural identity fields. The label is deliberately
        # generic, so a lookup's selected-customer caption is never requested.
        automation_id = _text(getattr(info, "automation_id", None))
        control_type = _text(getattr(info, "control_type", None)).casefold()
        runtime_id = _runtime_id(getattr(info, "runtime_id", None))
        visible = bool(getattr(info, "visible", True))

        if (
            automation_id != GRID_AUTOMATION_ID
            or control_type != GRID_CONTROL_TYPE
            or not visible
            or not runtime_id
        ):
            raise RuntimeError("windowhub_grid_identity_invalid")

        observation = EnvironmentObservation(
            state=EnvironmentState(
                active_application="WindowHub",
                active_window_title=title,
            ),
            metadata={
                "source": "windowhub",
                "window_handle": window_handle,
            },
        )

        target = ScreenElement(
            kind="table",
            label="Tabela danych",
            confidence=0.99,
            interaction_capability=InteractionCapability.NOT_INTERACTIVE,
            metadata={
                "source": "windowhub_ui_automation",
                "uia_control_type": control_type,
                "uia_runtime_id": runtime_id,
                "uia_visible": True,
            },
        )

        scene = ScreenScene(
            observation=observation,
            elements=(target,),
        )
        task_id = "windowhub-structure-smoke"
        world_revision = 1
        snapshot = AgentTaskV2WorldBuilder().build(
            scene,
            task_id=task_id,
            world_revision=world_revision,
        )

        provider = WindowHubUIAutomationProvider()
        reader = WindowHubUIAGridStructureReader(
            grid_resolver=lambda semantic_target: (
                provider.resolve_table_element(
                    semantic_target,
                    observation,
                )
            )
        )

        broker = ReadOnlyObservationBroker()
        spec = windowhub_grid_structure_capability_spec()
        broker.register(spec, reader)
        descriptor = broker.bind(
            snapshot,
            capability_name=spec.name,
            target_ref="ent_0001",
        )

        request = {
            "version": "2",
            "task_id": task_id,
            "goal": (
                "Inspect structural metadata of the currently open "
                "WindowHub lookup table without reading table cells."
            ),
            "intent": "computer_use",
            "session_id": None,
            "task_state": {
                "cycle": 1,
                "max_cycles": 1,
                "reasoning_calls_remaining": 0,
            },
            "world": dict(snapshot.payload),
            "capabilities": {
                "observations": [descriptor],
                "actions": [],
            },
            "knowledge": None,
            "experience": [],
            "constraints": {
                "max_observations_per_cycle": 1,
                "max_observation_items": 10,
                "max_evidence_bytes": 2_048,
                "semantic_only": True,
                "verify_each_action": True,
            },
            "metadata": {},
        }
        validate_agent_task_v2_payload(request)

        observation_request = {
            "capability_id": descriptor["id"],
            "target_ref": descriptor["target_ref"],
            "parameters": {
                "fields": [
                    "row_count",
                    "column_count",
                    "grid_pattern_available",
                    "table_pattern_available",
                ]
            },
            "based_on_world_revision": world_revision,
        }
        response = {
            "version": "2",
            "task_id": task_id,
            "decision": "observe",
            "rationale": (
                "Read only table structure; do not inspect rows or cells."
            ),
            "confidence": 1.0,
            "observation_request": observation_request,
            "action": None,
            "completion": None,
            "requires_manual_review": False,
        }
        validate_agent_task_v2_response(response, request)

        evidence = broker.observe(
            observation_request,
            task_id=task_id,
            world_revision=world_revision,
            max_observation_items=10,
            max_evidence_bytes=2_048,
        )

        result = {
            "result": "PASS",
            "windowhub_focused": True,
            "windowhub_brought_to_foreground_by_script": brought_to_foreground,
            "lookup_popup_opened_by_script": opened_by_script,
            "semantic_table_found": True,
            "observation_protocol": "v2",
            "observation_capability": descriptor["id"],
            "evidence_source": evidence["source"],
            "evidence_ref": evidence["ref"],
            "table_structure": evidence["content"]["fields"],
            "limitations": evidence["limitations"],
            "table_cells_read": 0,
            "column_header_text_read": 0,
            "customer_values_read": 0,
            "record_selected": False,
            "offer_saved": False,
            "planner_calls": 0,
            "remote_reasoning_calls": 0,
            "action_capabilities_exposed": 0,
        }

        if opened_by_script and lookup is not None:
            cleanup_ok = _close_lookup_popup(lookup)
            result["popup_escape_sent"] = cleanup_ok
        else:
            result["popup_escape_sent"] = False

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    except Exception as exc:
        if opened_by_script and lookup is not None:
            cleanup_ok = _close_lookup_popup(lookup)
        print(
            f"result: FAIL ({type(exc).__name__}: {exc})",
            file=sys.stderr,
        )
        if cleanup_ok is not None:
            print(f"popup_cleanup_escape_sent: {cleanup_ok}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
