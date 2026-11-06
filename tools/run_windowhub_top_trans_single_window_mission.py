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
from app.agent.offers.windowhub_customer_search_action import type_directly_into_customer_lookup
from app.agent.offers.windowhub_document_properties_action import (
    DOCUMENT_PRICE_AUTOMATION_IDS, prepare_price_exclusion,
)
from app.agent.offers.windowhub_offer_form_action import (
    WindowHubOfferFormActionExecutor, WindowHubFormActionStatus,
    WindowHubOfferFormActionPlanner,
)
from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap
from app.agent.offers.windowhub_offer_form_plan import WindowHubPlannedField, WindowHubPlanHandling
from app.agent.offers.windowhub_wizard_navigation import WindowHubPositionToDimensionsPlanner
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
    # The control loop may return a rich result without a simple success flag.
    # Always require the caller to freshly check a business postcondition.
    return True


def verify_exclusion(scene, key):
    observed = matches(scene, kind="checkbox",
                       automation_id=DOCUMENT_PRICE_AUTOMATION_IDS[key])
    return len(observed) == 1 and (observed[0].metadata or {}).get("uia_checked") is True


def customer_selected(scene):
    # The existing customer lookup does not reliably expose the selected value.
    # Never interpret a focused button or opened grid as a selected client.
    candidates = matches(scene, automation_id="IDC_ZAMAWIAJACY")
    if len(candidates) != 1:
        return False
    value = (candidates[0].metadata or {}).get("current_value")
    return isinstance(value, str) and value.strip().casefold() == CUSTOMER.casefold()


def handle_customer_lookup(scene):
    """Find and click exactly one same-process native customer result."""
    from app.agent.offers.windowhub_customer_result_selection import (
        select_exact_customer_result,
    )
    return select_exact_customer_result(scene, CUSTOMER)


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
    if not isinstance(rid, str) or not rid:
        return False
    from app.agent.perception.windowhub_ui_automation_provider import WindowHubUIAutomationProvider
    for item in Desktop(backend="uia").window(handle=hwnd).wrapper_object().descendants():
        try:
            if (str(item.element_info.automation_id) == DOCUMENT_PRICE_AUTOMATION_IDS[key]
                    and WindowHubUIAutomationProvider._runtime_id(item) == rid
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


def select_catalog_option_once(scene, *, field_name, approved_options):
    """Choose one exact native ComboBox option; no substring or first-row guessing."""
    from pywinauto import Desktop
    snapshot = WindowHubOfferFormMap().inspect(scene)
    match = snapshot.field(field_name) if snapshot else None
    if (match is None or not match.is_unique or match.enabled is not True
            or match.element.kind != "combobox"):
        print("STOP = catalog combo unavailable", field_name)
        return False
    target = match.element
    meta = target.metadata or {}
    if not isinstance(meta.get("uia_runtime_id"), str):
        print("STOP = catalog combo has no stable runtime identity")
        return False
    from app.agent.perception.windowhub_ui_automation_provider import WindowHubUIAutomationProvider
    hwnd = scene.observation.metadata.get("window_handle")
    if not isinstance(hwnd, int) or hwnd <= 0:
        return False
    candidates = []
    for item in Desktop(backend="uia").window(handle=hwnd).wrapper_object().descendants():
        try:
            if (str(item.element_info.control_type).casefold() == "combobox"
                    and str(item.element_info.automation_id) == meta["automation_id"]
                    and WindowHubUIAutomationProvider._runtime_id(item) == meta["uia_runtime_id"]
                    and bool(item.element_info.enabled)
                    and bool(item.element_info.visible)):
                candidates.append(item)
        except Exception:
            continue
    if len(candidates) != 1:
        print("STOP = catalog native combo ambiguous", field_name, len(candidates))
        return False
    wrapper = candidates[0]
    try:
        options = [str(v).strip() for v in wrapper.item_texts()]
    except Exception as exc:
        print("STOP = catalog options unreadable", type(exc).__name__)
        return False
    allowed = {v.casefold() for v in approved_options}
    available = [option for option in options if option.casefold() in allowed]
    print("CATALOG_FIELD =", field_name)
    print("CATALOG_OPTION_COUNT =", len(options))
    print("APPROVED_EXACT_MATCHES =", len(available))
    if len(available) != 1:
        return False
    desired = available[0]
    try:
        wrapper.select(desired)
    except Exception as exc:
        print("STOP = catalog selection unavailable", type(exc).__name__)
        return False
    return True


def advance_known_wizard(scene, *, expected_stage):
    """Click one unique Next control and rely on caller's stage re-observation."""
    buttons = matches(scene, kind="button", label="Dalej >", automation_id="12324")
    if len(buttons) != 1:
        print("STOP = no unique next button")
        return False
    try:
        native = resolve_native_wrapper(
            scene, label="Dalej >", automation_id="12324",
            allowed_stages=(stage_of(scene),),
        )
        try:
            invoke = native.iface_invoke
        except Exception:
            invoke = None
        if invoke is not None:
            invoke.Invoke()
        else:
            native.click_input()
        return True
    except Exception as exc:
        print("STOP = next stage", expected_stage, type(exc).__name__)
        return False


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

        if stage == "offer_document" and actions > 0:
            print("REASON = Document properties confirmed; add a new window position")
            approved = ("Nowa pozycja", "Dodaj nową pozycję", "Dodawanie nowej pozycji")
            candidates = [e for e in scene.elements
                          if e.kind == "button"
                          and (e.label or "").strip().casefold() in {
                              label.casefold() for label in approved
                          }
                          and (e.metadata or {}).get("uia_visible") is True
                          and (e.metadata or {}).get("uia_enabled") is True]
            print("NEW_POSITION_NATIVE_CANDIDATES =", len(candidates))
            if len(candidates) != 1:
                print("STOP = new position control not uniquely exposed")
                return 6
            try:
                wrapper = resolve_native_wrapper(
                    scene, label=candidates[0].label,
                    automation_id=(candidates[0].metadata or {}).get("automation_id"),
                    allowed_stages=("offer_document",),
                )
                try:
                    invocation = wrapper.iface_invoke
                except Exception:
                    invocation = None
                if invocation is None:
                    wrapper.click_input()
                else:
                    invocation.Invoke()
            except Exception as exc:
                print("STOP = new position activation", type(exc).__name__)
                return 6
            actions += 1
            if observe_step(loop, "position") is None:
                print("STOP = position wizard did not open")
                return 6
            continue

        if stage == "document_properties":
            if not customer_selected(scene):
                print("REASON = Top Trans must be selected before confirming offer")
                # DevExpress LookUpEdit: write directly at the verified
                # text area, not a guessed dropdown child or first grid row.
                search = type_directly_into_customer_lookup(scene, CUSTOMER)
                print("CUSTOMER_SEARCH_STATUS =", search.status)
                print("CUSTOMER_SEARCH_REASON =", search.reason)
                if search.status != "search_submitted_unverified":
                    print("STOP = CUSTOMER_DIRECT_LOOKUP_INPUT_NOT_VERIFIED")
                    print("NO_BLIND_RETRY = True")
                    return 6
                actions += 1
                queried = inspect(loop)
                print("CUSTOMER_AFTER_SEARCH_SELECTED =", customer_selected(queried))
                if customer_selected(queried):
                    continue
                ok, reason = handle_customer_lookup(queried)
                print("CUSTOMER_LOOKUP_RESULT =", reason)
                if not ok and reason == "EXACT_CUSTOMER_RESULT_NOT_UNIQUE_OR_NOT_VISIBLE":
                    # Text input and opening the dropdown are different
                    # operations in the native LookUpEdit widget.
                    from app.agent.offers.windowhub_customer_result_selection import (
                        reveal_customer_results,
                    )
                    opened, open_reason = reveal_customer_results(queried)
                    print("CUSTOMER_DROPDOWN_RESULT =", open_reason)
                    if opened:
                        actions += 1
                        time.sleep(0.25)
                        after_dropdown = inspect(loop)
                        if stage_of(after_dropdown) == "document_properties":
                            ok, reason = handle_customer_lookup(after_dropdown)
                            print("CUSTOMER_LOOKUP_AFTER_DROPDOWN =", reason)
                if ok:
                    actions += 1
                    fresh = inspect(loop)
                    if customer_selected(fresh):
                        print("CUSTOMER_SELECTED_VERIFIED = True")
                        continue
                    print("CUSTOMER_EXACT_CLICK_DONE_BUT_SELECTED_VALUE_UNAVAILABLE = True")
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
            # Three price exclusions requested, not the older fourth
            # 'without construction price'. Confirm ONLY exact customer and
            # exactly these three settings as independently reobserved.
            final = inspect(loop)
            if not customer_selected(final) or not all(
                verify_exclusion(final, key) for key in EXCLUSIONS
            ):
                print("STOP = DOCUMENT_POSTCONDITIONS_MISSING")
                return 6
            buttons = matches(final, kind="button", label="OK")
            if len(buttons) != 1:
                print("STOP = DOCUMENT_OK_NOT_UNIQUE", len(buttons))
                return 6
            print("REASON = Top Trans and three requested price exclusions verified")
            try:
                button = resolve_native_wrapper(
                    final, label="OK",
                    allowed_stages=("document_properties",),
                )
                try:
                    pattern = button.iface_invoke
                except Exception:
                    pattern = None
                if pattern is not None:
                    pattern.Invoke()
                else:
                    button.click_input()
            except Exception as exc:
                print("STOP = DOCUMENT_CONFIRMATION_FAILED", type(exc).__name__)
                return 6
            actions += 1
            changed = inspect(loop)
            print("POST_DOCUMENT_STAGE =", stage_of(changed))
            if stage_of(changed) == "document_properties":
                print("STOP = document confirmation not verified")
                return 6
            continue

        if stage in ("windowhub_unmapped", "customer_lookup"):
            ok, reason = handle_customer_lookup(scene)
            print("CUSTOMER_LOOKUP_RESULT =", reason)
            print("STOP = CUSTOMER_SELECTION_UNVERIFIED")
            return 6

        if stage == "position":
            print("REASON = configure one window position, not a sill or shutter")
            snapshot = WindowHubOfferFormMap().inspect(scene)
            if snapshot is None:
                print("STOP = position wizard not uniquely mapped")
                return 6
            required = (
                ("item_type_window", True, WindowHubPlanHandling.RADIO_SELECTION),
                ("quantity_input", TARGET["quantity"], WindowHubPlanHandling.DIRECT_VALUE),
            )
            did = False
            for key, desired, handling in required:
                fresh = inspect(loop)
                entry = WindowHubPlannedField(
                    field_name=key, desired_value=desired,
                    source="requested_test_window", handling=handling,
                )
                prepared = WindowHubOfferFormActionPlanner().prepare_entry(fresh, entry)
                if prepared.status is WindowHubFormActionStatus.READY:
                    if not execute_prepared(prepared, fresh, loop, "Set " + key):
                        print("STOP = position action blocked", key)
                        return 6
                    actions += 1
                    verified_scene = inspect(loop)
                    check = WindowHubOfferFormActionPlanner().prepare_entry(
                        verified_scene, entry
                    )
                    if check.status is not WindowHubFormActionStatus.ALREADY_SATISFIED:
                        print("STOP = position field postcondition not verified", key, check.reason)
                        return 6
                    print("POSTCONDITION_VERIFIED =", key)
                    did = True
                    break
                if prepared.status is not WindowHubFormActionStatus.ALREADY_SATISFIED:
                    print("STOP = position field blocked", key, prepared.reason)
                    return 6
            if did:
                continue
            prepared = WindowHubPositionToDimensionsPlanner().prepare(
                scene, expected_quantity=TARGET["quantity"]
            )
            if not execute_prepared(
                prepared, scene, loop, "Advance from position to dimensions"
            ):
                print("STOP = position navigation blocked")
                return 6
            actions += 1
            if observe_step(loop, "dimensions") is None:
                print("STOP = dimensions stage not verified")
                return 6
            continue

        if stage == "dimensions":
            print("REASON = set actual full-window width and height")
            changed = False
            for key, desired in (("width_1", TARGET["width_mm"]),
                                 ("height_1", TARGET["height_mm"])):
                fresh = inspect(loop)
                entry = WindowHubPlannedField(
                    field_name=key, desired_value=desired,
                    source="requested_test_window",
                    handling=WindowHubPlanHandling.DIRECT_VALUE,
                )
                prepared = WindowHubOfferFormActionPlanner().prepare_entry(fresh, entry)
                if prepared.status is WindowHubFormActionStatus.READY:
                    if not execute_prepared(prepared, fresh, loop, "Set " + key):
                        return 6
                    actions += 1
                    verified_scene = inspect(loop)
                    check = WindowHubOfferFormActionPlanner().prepare_entry(
                        verified_scene, entry
                    )
                    if check.status is not WindowHubFormActionStatus.ALREADY_SATISFIED:
                        print("STOP = dimension postcondition not verified", key, check.reason)
                        return 6
                    print("POSTCONDITION_VERIFIED =", key)
                    changed = True
                    break
                if prepared.status is not WindowHubFormActionStatus.ALREADY_SATISFIED:
                    print("STOP = dimension unmapped or unsafe", key, prepared.reason)
                    return 6
            if changed:
                continue
            button = matches(scene, kind="button", label="Dalej >", automation_id="12324")
            if len(button) != 1:
                print("STOP = dimensions next control not unique")
                return 6
            try:
                native = resolve_native_wrapper(
                    scene, label="Dalej >", automation_id="12324",
                    allowed_stages=("dimensions",)
                )
                native.click_input()
            except Exception as exc:
                print("STOP = dimensions next", type(exc).__name__)
                return 6
            actions += 1
            fresh = inspect(loop)
            if stage_of(fresh) != "basic_parameters":
                print("STOP = basic parameters not verified", stage_of(fresh))
                return 6
            continue

        if stage == "basic_parameters":
            print("REASON = choose anthracite profile using an exact observed catalog option")
            profile = WindowHubOfferFormMap().inspect(scene)
            selected = profile.field("profile_color") if profile else None
            actual = (selected.element.metadata or {}).get("current_value") if selected and selected.is_unique else None
            exact_colors = ("Antracyt", "Antracyt / Antracyt", "Antracyt obustronny",
                            "RAL 7016 obustronnie", "Antracyt / antracyt (RAL 7016)")
            if not isinstance(actual, str) or actual.strip().casefold() not in {
                value.casefold() for value in exact_colors
            }:
                if not select_catalog_option_once(
                    scene, field_name="profile_color", approved_options=exact_colors
                ):
                    print("STOP = anthracite catalog option not safely selectable")
                    return 6
                actions += 1
                after = inspect(loop)
                field = WindowHubOfferFormMap().inspect(after)
                selected = field.field("profile_color") if field else None
                actual = (selected.element.metadata or {}).get("current_value") if selected and selected.is_unique else None
                if not isinstance(actual, str) or actual.strip().casefold() not in {
                    value.casefold() for value in exact_colors
                }:
                    print("STOP = anthracite UIA value not confirmed")
                    return 6
                print("PROFILE_COLOR_VERIFIED =", actual)
                continue
            if not advance_known_wizard(scene, expected_stage="glazing"):
                print("STOP = basic parameters next step unavailable")
                return 6
            actions += 1
            result = inspect(loop)
            if stage_of(result) not in ("glazing", "hardware"):
                print("STOP = glazing/hardware step not verified", stage_of(result))
                return 6
            continue

        if stage == "glazing":
            print("REASON = choose three-pane glazing only from an exact catalog label")
            snapshot = WindowHubOfferFormMap().inspect(scene)
            glass = snapshot.field("glazing_package") if snapshot else None
            actual = (glass.element.metadata or {}).get("current_value") if glass and glass.is_unique else None
            glass_names = ("3glass", "3 szyby", "Pakiet trzyszybowy",
                           "Trzyszybowy", "3-szybowy")
            if not isinstance(actual, str) or actual.strip().casefold() not in {
                x.casefold() for x in glass_names
            }:
                if not select_catalog_option_once(
                    scene, field_name="glazing_package", approved_options=glass_names
                ):
                    print("STOP = triple glazing catalog mapping not verified")
                    return 6
                actions += 1
                fresh = inspect(loop)
                snapshot = WindowHubOfferFormMap().inspect(fresh)
                glass = snapshot.field("glazing_package") if snapshot else None
                actual = (glass.element.metadata or {}).get("current_value") if glass and glass.is_unique else None
                if not isinstance(actual, str) or actual.strip().casefold() not in {
                    x.casefold() for x in glass_names
                }:
                    print("STOP = glazing selection postcondition not verified")
                    return 6
                continue
            if not advance_known_wizard(scene, expected_stage="hardware"):
                print("STOP = glazing next step unavailable")
                return 6
            actions += 1
            observed = inspect(loop)
            if stage_of(observed) not in ("hardware", "modifier"):
                print("STOP = hardware/modifier not reached", stage_of(observed))
                return 6
            continue

        if stage in ("hardware", "modifier"):
            print("OBSERVED_CONSTRUCTION_STAGE =", stage)
            print("STOP = detailed hardware dialog and frame/sash creation require observed native choices")
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
    parser.add_argument("--customer-name", default="Top Trans",
                        help="Exact existing customer name extracted from a verified order")
    args = parser.parse_args(argv)
    global CUSTOMER
    if (not args.customer_name.strip() or len(args.customer_name.strip()) > 100
            or any(ord(ch) < 32 for ch in args.customer_name)):
        print("STOP = invalid requested customer name")
        return 2
    CUSTOMER = args.customer_name.strip()
    print("=== WINDOWHUB EXISTING CUSTOMER SINGLE WINDOW MISSION ===")
    print("MISSION =", CUSTOMER, TARGET)
    print("DECISION_SOURCE = deterministic_verified_policy")
    print("MODEL_REQUESTS = 0")
    print("FINAL_SAVE = disabled")
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
