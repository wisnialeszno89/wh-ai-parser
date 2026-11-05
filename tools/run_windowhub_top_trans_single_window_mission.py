"""One bounded WindowHub real-offer mission.

Launch from an already running Okna.exe (Start1 or document). Goal: Top Trans,
three price exclusions, one 1000x1200 anthracite triple-glazed RU window.
Uses existing guarded navigation and form actions, stops at unverified controls.
DOES NOT save, submit, or substitute a different client. One action per cycle.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
from app.agent.offers.windowhub_document_properties_action import (
    DOCUMENT_PRICE_AUTOMATION_IDS, prepare_price_exclusion,
)
from app.agent.offers.windowhub_offer_form_action import (
    WindowHubOfferFormActionExecutor, WindowHubFormActionStatus,
    WindowHubOfferFormActionPlanner,
)
from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap
from app.agent.offers.windowhub_offer_form_plan import WindowHubPlannedField, WindowHubPlanHandling
from app.agent.offers.windowhub_wizard_navigation import WindowHubWizardNavigationPlanner
from tools.run_windowhub_new_offer_native_invoke_once import resolve_native_control, resolve_native_wrapper

CUSTOMER = "Top Trans"
EXCLUSIONS = (
    "exclude_installation_price", "exclude_removal_price", "exclude_finishing_price",
)
TARGET = dict(quantity=1, width_mm=1000, height_mm=1200,
              color="antracyt", glazing="triple", opening="RU")
STEPS = ("start", "document_properties", "position", "dimensions",
         "basic_parameters", "glazing", "hardware", "modifier")
UIA_SOURCES = {"windows_ui_automation", "windowhub_ui_automation"}


def inspect(loop):
    return enrich_windowhub_scene(loop.observe_scene())


def matches(scene, *, kind=None, label=None, automation_id=None):
    return [
        e for e in scene.elements
        if (kind is None or e.kind == kind)
        and (label is None or (e.label or "").strip().casefold() == label.casefold())
        and (automation_id is None or (e.metadata or {}).get("automation_id") == automation_id)
        and (e.metadata or {}).get("source") in UIA_SOURCES
        and (e.metadata or {}).get("uia_visible") is True
        and (e.metadata or {}).get("uia_enabled") is True
    ]


def observe_step(loop, expected, attempts=4):
    for index in range(attempts):
        scene = inspect(loop)
        stage = stage_of(scene)
        print("POST_ACTION_STAGE =", stage, flush=True)
        if stage == expected:
            return scene
        if index + 1 < attempts:
            time.sleep(0.25)
    return None


def execute_prepared(prepared, scene, loop, description):
    print("PLAN =", description)
    print("PREPARED_STATUS =", prepared.status.value)
    print("PREPARED_REASON =", prepared.reason)
    if prepared.status is WindowHubFormActionStatus.ALREADY_SATISFIED:
        return True
    if prepared.status is not WindowHubFormActionStatus.READY:
        return False
    result = WindowHubOfferFormActionExecutor.execute_prepared(
        prepared, scene, loop, request_message=description,
    )
    print("EXECUTION_REPORT =", str(result)[:400])
    return True  # Re-observe exact postcondition before proceeding.


def verify_exclusion(scene, key):
    observed = matches(scene, kind="checkbox",
                       automation_id=DOCUMENT_PRICE_AUTOMATION_IDS[key])
    return len(observed) == 1 and (observed[0].metadata or {}).get("uia_checked") is True


def customer_selected(scene):
    # The existing customer lookup does not reliably expose the selected value.
    # Never interpret a focused button or opened grid as a selected client.
    for e in matches(scene, automation_id="IDC_ZAMAWIAJACY"):
        value = (e.metadata or {}).get("current_value")
        if isinstance(value, str) and value.strip().casefold() == CUSTOMER.casefold():
            return True
    return False


def handle_customer_lookup(scene):
    """Attempt exact customer selection only if the UIA element is unambiguous.

    Generic dropdowns do not expose reliable row identity on all WindowHub
    versions. Avoid selecting top/first rows by position or guessed text.
    """
    exact = [e for e in matches(scene) if e.kind in
             {"listitem", "dataitem", "treeitem", "button", "text"}
             and (e.label or "").strip().casefold() == CUSTOMER.casefold()]
    print("EXACT_CUSTOMER_VISIBLE_MATCHES =", len(exact))
    if len(exact) != 1:
        return False, "TOP_TRANS_ROW_NOT_UNIQUELY_VISIBLE"
    return False, "CUSTOMER_ROW_HAS_NO_VERIFIED_SELECTION_POSTCONDITION"


def toggle_price_once(scene, key):
    prepared = prepare_price_exclusion(scene, key)
    if prepared.status is WindowHubFormActionStatus.ALREADY_SATISFIED:
        print("PREFERENCE =", key, "ALREADY_SET")
        return True
    if prepared.status is not WindowHubFormActionStatus.READY:
        print("STOP_PREFERENCE =", key, prepared.reason)
        return False
    # Strictly rebind unique native checkbox before toggle; native TogglePattern
    # changes only the one observed field. Verify via fresh UIA observation.
    from pywinauto import Desktop
    hwnd = scene.observation.metadata.get("window_handle")
    if not isinstance(hwnd, int):
        return False
    found = []
    target = matches(scene, kind="checkbox",
                     automation_id=DOCUMENT_PRICE_AUTOMATION_IDS[key])
    if len(target) != 1:
        return False
    rid = (target[0].metadata or {}).get("uia_runtime_id")
    for item in Desktop(backend="uia").window(handle=hwnd).wrapper_object().descendants():
        try:
            if (str(item.element_info.automation_id) == DOCUMENT_PRICE_AUTOMATION_IDS[key]
                    and bool(item.element_info.enabled)
                    and bool(item.element_info.visible)):
                found.append(item)
        except Exception:
            continue
    if len(found) != 1:
        print("STOP = pricing native target ambiguous", key)
        return False
    native = found[0]
    try:
        pattern = native.iface_toggle
        if pattern is None or int(pattern.CurrentToggleState) != 0:
            print("STOP = no reliable unchecked TogglePattern")
            return False
        pattern.Toggle()
    except Exception as exc:
        print("STOP_TOGGLE =", type(exc).__name__)
        return False
    return True


def mission(loop, max_actions):
    actions = 0
    visited = []
    for iteration in range(max_actions):
        scene = inspect(loop)
        stage = stage_of(scene)
        visited.append(stage)
        print(f"\n=== STEP {iteration + 1} / {max_actions} ===")
        print("OBSERVED_STAGE =", stage)
        print("GOAL =", CUSTOMER, TARGET)
        if stage is None:
            print("STOP = WindowHub not foreground")
            return 4
        if stage in ("start", "offer_document") and actions == 0:
            print("REASON = New offer must be opened before customer selection")
            try:
                resolve_native_control(
                    scene, label="NOWA OFERTA",
                    allowed_stages=(stage,),
                ).Invoke()
            except Exception as exc:
                print("STOP = OPEN_NEW_OFFER", type(exc).__name__, str(exc)[:140])
                return 6
            actions += 1
            if observe_step(loop, "document_properties") is None:
                print("STOP = document properties not verified")
                return 6
            continue

        if stage == "document_properties":
            if not customer_selected(scene):
                print("REASON = Top Trans must be selected before confirming offer")
                try:
                    wrapper = resolve_native_wrapper(
                        scene, label="Wybierz istniejącego klienta",
                        automation_id="IDC_ZAMAWIAJACY",
                        allowed_stages=("document_properties",),
                    )
                    wrapper.click_input()
                except Exception as exc:
                    print("STOP = CUSTOMER_LOOKUP_OPEN", type(exc).__name__, str(exc)[:140])
                    return 6
                actions += 1
                after = inspect(loop)
                selected = customer_selected(after)
                print("CUSTOMER_SELECTED_VERIFIED =", selected)
                if selected:
                    continue
                ok, reason = handle_customer_lookup(after)
                print("CUSTOMER_LOOKUP_RESULT =", reason)
                print("STOP = CUSTOMER_SELECTION_UNVERIFIED")
                print("NO_BLIND_RETRY = True")
                return 6
            print("CUSTOMER_SELECTED_VERIFIED = True")
            for key in EXCLUSIONS:
                current = inspect(loop)
                if stage_of(current) != "document_properties":
                    print("STOP = pricing stage changed")
                    return 6
                if verify_exclusion(current, key):
                    print("PREFERENCE =", key, "ALREADY_SET")
                    continue
                print("REASON = enable", key)
                if not toggle_price_once(current, key):
                    print("STOP = PREFERENCE_ACTION_UNVERIFIED", key)
                    return 6
                actions += 1
                fresh = inspect(loop)
                if not verify_exclusion(fresh, key):
                    print("STOP = PREFERENCE_POSTCONDITION_MISSING", key)
                    return 6
                print("PREFERENCE =", key, "VERIFIED")
            # A final OK is intentionally gated: in old missions user requested
            # 'without construction price' too, which we do NOT apply here.
            # Exact three-price policy must be checked against live scene.
            print("DOCUMENT_PREFERENCES_VERIFIED = True")
            print("STOP = DOCUMENT_CONFIRMATION_NOT_YET_MAPPED_FOR_THREE_EXCLUSIONS")
            return 4

        if stage in ("windowhub_unmapped", "customer_lookup"):
            ok, reason = handle_customer_lookup(scene)
            print("CUSTOMER_LOOKUP_RESULT =", reason)
            print("STOP = CUSTOMER_SELECTION_UNVERIFIED")
            return 6

        if stage in ("position", "dimensions", "basic_parameters", "glazing", "hardware", "modifier"):
            print("POSITION_STAGE_REACHED =", stage)
            print("NEXT = continue via existing wizard actions only after document customer confirmation")
            return 4

        print("STOP = unknown stage")
        return 4
    print("STOP = action budget exhausted")
    print("EXECUTED_ACTIONS =", actions)
    return 4


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--max-actions", type=int, default=16)
    args = parser.parse_args(argv)
    print("=== WINDOWHUB TOP TRANS SINGLE WINDOW MISSION ===")
    print("MISSION =", CUSTOMER, TARGET)
    if not 1 <= args.max_actions <= 24:
        return 2
    if os.name != "nt":
        return 2
    if os.environ.get("WH_REAL_WINDOWHUB") != "1" or os.environ.get("COMPUTER_USE_LIVE") != "1":
        print("STOP = explicit live authorization required")
        return 2
    if not args.execute_live:
        print("PLAN_ONLY = True")
        print("ACTION_COUNT = 0")
        return 0
    ok, reason = activate_windowhub_workflow_window()
    print("AUTO_ACTIVATION =", ok)
    if not ok:
        print("STOP =", reason)
        return 4
    try:
        return mission(create_windows_desktop_agent_control_loop(), args.max_actions)
    except Exception as exc:
        print("STOP = UNHANDLED", type(exc).__name__, str(exc)[:160])
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
