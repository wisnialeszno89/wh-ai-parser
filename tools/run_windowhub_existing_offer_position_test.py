"""Add a test position to an explicitly identified, disposable WindowHub offer."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.runtime.windowhub_catalog_continuation import (
    catalog_options_for, dimensions_match, exact_selected,
)
from app.agent.runtime.windowhub_mdi_native_probe import _Win32Mdi, offer_caption_id, same_offer_id
from tools.run_navimind_whokna_first_verified_step import test_offer_diagnostic as offer_diagnostic
from tools.run_windowhub_new_offer_native_invoke_once import resolve_native_wrapper
from tools.run_windowhub_sales_offer_live import open_verified_position
from tools.run_windowhub_top_trans_single_window_mission import inspect, matches, select_catalog_label_once

WIDTH, HEIGHT, QUANTITY = 1500, 1400, 1
_WIZARDS = {"position", "dimensions", "basic_parameters", "glazing", "hardware", "modifier"}
_NEXT_STAGES = {
    "position": {"dimensions"},
    "dimensions": {"basic_parameters"},
    "basic_parameters": {"glazing", "hardware", "modifier", "offer_document"},
    "glazing": {"hardware", "modifier", "offer_document"},
    "hardware": {"modifier", "offer_document"},
}


def foreground_offer_caption(scene, api):
    """Read the offer caption from the current document or its foreground wizard owner."""
    stage = stage_of(scene)
    hwnd = scene.observation.metadata.get("window_handle")
    if type(hwnd) is not int or hwnd <= 0 or api.foreground() != hwnd:
        return None
    if stage == "offer_document":
        title = (scene.observation.state.active_window_title or "").strip()
    elif stage in _WIZARDS:
        owner = api.parent(hwnd, 3)  # GA_ROOTOWNER
        title = api.title(owner).strip() if owner and owner != hwnd else ""
    else:
        return None
    if title.casefold().startswith("okna - ofr/") and offer_caption_id(title[7:]) is not None:
        return title[7:]
    return None


def belongs_to_offer(scene, offer, api):
    caption = foreground_offer_caption(scene, api)
    if not same_offer_id(caption, offer):
        return False
    if stage_of(scene) == "offer_document":
        return offer_diagnostic(scene, offer)["selected_offer_matches_requested"]
    return True


def confirm_stage(loop, scene, offer, api):
    """Invoke a single affirmative control of the current wizard and check its destination."""
    stage = stage_of(scene)
    allowed = _NEXT_STAGES.get(stage)
    if not allowed or not belongs_to_offer(scene, offer, api):
        return None
    buttons = [
        b for b in matches(scene, kind="button")
        if (b.label or "").strip().casefold() in {"dalej >", "ok", "zakończ", "zakoncz"}
        and (b.metadata or {}).get("automation_id")
    ]
    if len(buttons) > 1 and stage in {"position", "dimensions", "basic_parameters", "glazing"}:
        next_buttons = [
            b for b in buttons
            if b.label.strip().casefold() == "dalej >"
            and b.metadata["automation_id"] == "12324"
        ]
        if len(next_buttons) == 1:
            buttons = next_buttons
    if len(buttons) != 1:
        print(f"TEST_CONFIRM_BLOCKED={stage}:affirmative_control_count_{len(buttons)}")
        return None
    button = buttons[0]
    control_id = button.metadata["automation_id"]
    try:
        wrapper = resolve_native_wrapper(
            scene, label=button.label, automation_id=control_id, allowed_stages=(stage,),
        )
        try:
            invoke = wrapper.iface_invoke
        except Exception:
            invoke = None
        if not belongs_to_offer(scene, offer, api):
            return None
        print(f"TEST_CONFIRM_ATTEMPT={stage}:{button.label}", flush=True)
        if invoke is not None:
            invoke.Invoke()
        else:
            wrapper.click_input()
    except Exception as exc:
        print("TEST_CONFIRM_EFFECT_UNKNOWN=" + type(exc).__name__)
        return None
    for i in range(7):
        after = inspect(loop)
        destination = stage_of(after)
        owner_matches = belongs_to_offer(after, offer, api)
        print(f"TEST_CONFIRM_OBSERVED={destination}:owner_match_{owner_matches}")
        if destination in allowed and owner_matches:
            print(f"TEST_CONFIRM_VERIFIED={stage}->{destination}")
            return after
        # A capture may have started before the modal changed. If the old
        # HWND lost focus during that capture, take a fresh observation.
        # Only a recognized destination with matching OFR can succeed.
        if destination not in {stage, "windowhub_unmapped"} and destination not in allowed:
            break
        if destination == "offer_document" and not owner_matches:
            break
        if i < 6:
            time.sleep(0.4)
    print("TEST_CONFIRM_UNVERIFIED=" + stage)
    return None


def choose_catalog(loop, scene, offer, api, field, options, *, accepted_defaults=()):
    if not belongs_to_offer(scene, offer, api):
        return None
    if exact_selected(scene, field, options + accepted_defaults):
        from app.agent.runtime.windowhub_catalog_handoff import current_catalog_value
        print(f"TEST_CATALOG_ALREADY_SELECTED={field}:{current_catalog_value(scene, field)!r}")
        return scene
    label = select_catalog_label_once(
        scene, field_name=field, approved_options=options + accepted_defaults,
        allow_test_catalog_choice=True,
    )
    if label is None:
        return None
    print(f"TEST_CATALOG_REQUESTED={field}:{label!r}")
    for attempt in range(3):
        after = inspect(loop)
        if stage_of(after) != stage_of(scene) or not belongs_to_offer(after, offer, api):
            break
        if exact_selected(after, field, (label,)):
            print(f"TEST_CATALOG_READBACK={field}:{label!r}")
            return after
        if attempt < 2:
            time.sleep(0.25)
    return None


def stop(reason):
    print("TEST_STOP=" + reason)
    return 4


def run(loop, offer, api, *, stop_at_editor=False):
    from tools.run_windowhub_local_select_window_once import run as select_window
    from tools.run_windowhub_local_quantity_once import run as set_quantity
    from tools.run_windowhub_local_dimensions_once import run as set_dimensions

    scene = inspect(loop)
    stage = stage_of(scene)
    print("TEST_ENTRY_STAGE=" + str(stage))
    if not belongs_to_offer(scene, offer, api):
        return stop("requested_offer_or_wizard_owner_unverified")
    if stage == "offer_document":
        if not open_verified_position(loop, scene):
            return stop("add_unverified")
        scene = inspect(loop)
        stage = stage_of(scene)
        if stage != "position" or not belongs_to_offer(scene, offer, api):
            return stop("position_wizard_owner_unverified")
    if stage == "position":
        for name, action in (
            ("window_type", lambda: select_window(live=True)),
            ("quantity", lambda: set_quantity(QUANTITY, live=True)),
        ):
            active = inspect(loop)
            if stage_of(active) != "position" or not belongs_to_offer(active, offer, api):
                return stop("position_wizard_owner_changed")
            if action() != 0:
                return stop(name + "_unverified")

        from app.agent.offers.windowhub_wizard_navigation import WindowHubPositionToDimensionsPlanner
        from app.agent.offers.windowhub_offer_form_action import WindowHubFormActionStatus
        from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap
        from tools.run_windowhub_local_quantity_once import observed_quantity

        scene = inspect(loop)
        snapshot = WindowHubOfferFormMap().inspect(scene)
        window = snapshot.field("item_type_window") if snapshot else None
        if (
            not window or not window.is_unique or window.element is None
            or (window.element.metadata or {}).get("uia_selected") is not True
            or observed_quantity(scene) != str(QUANTITY)
        ):
            return stop("position_readback_unverified")
        next_button = matches(scene, kind="button", label="Dalej >", automation_id="12324")
        if next_button and WindowHubPositionToDimensionsPlanner().prepare(
            scene, expected_quantity=QUANTITY,
        ).status is not WindowHubFormActionStatus.READY:
            return stop("position_next_binding_unverified")
        scene = confirm_stage(loop, scene, offer, api)
        if scene is None:
            return stop("position_confirmation_unverified")
        stage = stage_of(scene)

    if stage == "dimensions":
        if not belongs_to_offer(scene, offer, api):
            return stop("dimensions_wizard_owner_unverified")
        if set_dimensions(WIDTH, HEIGHT, execute_live=True) != 0:
            return stop("dimensions_unverified")
        scene = inspect(loop)
        if not dimensions_match(scene, width=WIDTH, height=HEIGHT):
            return stop("dimensions_readback_mismatch")
        scene = confirm_stage(loop, scene, offer, api)
        if scene is None:
            return stop("dimensions_confirmation_unverified")
        stage = stage_of(scene)

    colors, glazing = catalog_options_for(outside="antracyt", inside="biały", glazing_panes=2)
    color_verified = glazing_verified = False
    if stage == "basic_parameters":
        scene = choose_catalog(
            loop, scene, offer, api, "profile_color", colors,
            accepted_defaults=("Biały", "Biały / Biały", "BIAŁY CZARNA USZCZELKA"),
        )
        if scene is None:
            return stop("profile_color_selection_or_readback_unverified")
        color_verified = True
        print("TEST_PROFILE_COLOR_VERIFIED=True")
        scene = confirm_stage(loop, scene, offer, api)
        if scene is None:
            return stop("basic_parameters_confirmation_unverified")
        stage = stage_of(scene)

    if stage == "glazing":
        scene = choose_catalog(loop, scene, offer, api, "glazing_package", glazing)
        if scene is None:
            return stop("glazing_selection_or_readback_unverified")
        glazing_verified = True
        print("TEST_GLAZING_VERIFIED=True")
        scene = confirm_stage(loop, scene, offer, api)
        if scene is None:
            return stop("glazing_confirmation_unverified")
        stage = stage_of(scene)

    if stage == "hardware":
        if not glazing_verified:
            return stop("glazing_not_observed_before_hardware")
        # This test accepts the wizard's defaults. Require an observable
        # profile and group before committing those defaults.
        from app.agent.runtime.windowhub_catalog_handoff import current_catalog_value
        values = [current_catalog_value(scene, field) for field in ("hardware_profile", "hardware_group")]
        if not all(v and v.casefold() not in {"-", "—", "brak", "(brak)"} and
                   not v.casefold().startswith("wybierz") for v in values):
            return stop("hardware_defaults_unverified")
        scene = confirm_stage(loop, scene, offer, api)
        if scene is None:
            return stop("hardware_confirmation_unverified")
        stage = stage_of(scene)

    print("TEST_FINAL_STAGE=" + str(stage))
    print("TEST_CATALOG_READBACK_COMPLETE=" + str(color_verified and glazing_verified))
    if not glazing_verified and stage in {"modifier", "offer_document"}:
        print("TEST_GLAZING_WIZARD_NOT_OBSERVED=True")
    # Returning to the same offer proves navigation, but not an added row.
    # Modifier may open with an unbuilt frame. Do not accept an empty editor.
    if stage == "modifier":
        if stop_at_editor and color_verified and belongs_to_offer(scene, offer, api):
            print("TEST_RESULT=construction_editor_reached")
            return 0
        return stop("construction_editor_reached_position_commit_unverified")
    if stage == "offer_document":
        return stop("returned_to_requested_offer_new_row_unverified")
    return stop("unsupported_stage")


def run_from_start(loop, customer, api):
    from app.agent.runtime.windowhub_document_core import run_document_core
    from tools.run_windowhub_new_offer_entry import main as open_offer

    if stage_of(inspect(loop)) != "start":
        return stop("expected_start1_before_new_offer")
    if open_offer(["--execute-live"]) != 0:
        return stop("new_offer_entry_unverified")
    confirmed = []

    def capture(scene):
        caption = foreground_offer_caption(scene, api)
        if caption and belongs_to_offer(scene, caption, api):
            confirmed.append(caption)

    code = run_document_core(
        customer_name=customer, fresh_document=True, on_confirmed=capture,
    )
    if code != 0:
        return stop("customer_prices_or_document_confirmation_unverified")
    if len(confirmed) != 1:
        return stop("created_offer_identity_unverified")
    offer = confirmed[0]
    print("TEST_DOCUMENT_CONFIRMED=True")
    print("TEST_TARGET_OFFER=" + offer)
    return run(loop, offer, api, stop_at_editor=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--from-start", action="store_true",
                        help="Create one test offer from Start1 for an existing test customer")
    parser.add_argument("--start-delay", type=int, default=12, choices=range(0, 31), metavar="0..30")
    args = parser.parse_args(argv)
    if os.name != "nt" or not args.execute_live:
        return stop("windows_and_explicit_live_test_required")
    if any(os.environ.get(name) != "1" for name in ("COMPUTER_USE_LIVE", "WH_REAL_WINDOWHUB")):
        return stop("desktop_access_not_authorized")
    try:
        target = input(
            "Dokładna nazwa istniejącego klienta testowego: " if args.from_start
            else "Numer otwartej oferty testowej (OFR/…): "
        ).strip()
    except (EOFError, KeyboardInterrupt):
        return stop("no_test_target_provided")
    if args.from_start:
        if not target or len(target) > 100 or any(ord(ch) < 32 for ch in target):
            return stop("invalid_test_customer_name")
    elif offer_caption_id(target) is None:
        return stop("invalid_test_offer_number")
    print(f"Przejdz do WindowHub. Start za {args.start_delay} s.", flush=True)
    time.sleep(args.start_delay)
    from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
    loop = create_windows_desktop_agent_control_loop()
    api = _Win32Mdi()
    return run_from_start(loop, target, api) if args.from_start else run(loop, target, api)


if __name__ == "__main__":
    raise SystemExit(main())
