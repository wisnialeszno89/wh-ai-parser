"""Create an open test offer with two constructions and an intervening discount."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.runtime.windowhub_mdi_native_probe import _Win32Mdi, same_offer_id
from tools.run_windowhub_existing_offer_position_test import (
    belongs_to_offer, handoff_scene, inspect, matches, run, run_from_start,
)
from tools.run_windowhub_new_offer_native_invoke_once import resolve_native_wrapper
from tools.run_windowhub_sales_offer_live import open_verified_position

_DISCOUNT_LABELS = {"rabat", "rabat [%]", "rabat (%)", "rabat %"}
_DISCOUNT_TITLES = {"rabat", "rabaty", "wprowadzenie rabatu", "ustawienie rabatu"}
_DISCOUNT_TEXT = re.compile(r"18(?:[,.]0+)?\s*%?")


@dataclass(frozen=True)
class Position:
    width: int
    height: int
    left_opening: str
    right_opening: str | None = None
    split_from_left_mm: int | None = None

    def instruction(self):
        if self.right_opening is None:
            return f"jedno skrzydło {self.left_opening} (lewe rozwierno-uchylne)"
        return (
            f"dwa skrzydła, pionowy słupek stały na środku ({self.split_from_left_mm} mm), "
            f"lewe {self.left_opening} i prawe {self.right_opening}"
        )


POSITIONS = (
    Position(1000, 1000, "DKL"),
    Position(1500, 1400, "DKL", right_opening="DKR", split_from_left_mm=750),
)


def stop(reason):
    print("TWO_POSITION_STOP=" + reason, flush=True)
    return 4


def owned_discount(scene, offer, api):
    """Accept a discount modal only under the foreground test OFR."""
    hwnd = scene.observation.metadata.get("window_handle")
    if stage_of(scene) != "windowhub_unmapped" or type(hwnd) is not int or hwnd <= 0:
        return False
    if api.foreground() != hwnd:
        return False
    owner = api.parent(hwnd, 3)
    title = api.title(owner).strip() if owner and owner != hwnd else ""
    if not title.casefold().startswith("okna - ofr/") or not same_offer_id(title[7:], offer):
        return False
    caption = (scene.observation.state.active_window_title or "").strip().casefold()
    return caption in _DISCOUNT_TITLES or any(
        (element.metadata or {}).get("name", "").strip().rstrip(":").casefold() in _DISCOUNT_LABELS
        for element in matches(scene)
        if element.kind in {"edit", "text", "label"}
        and isinstance((element.metadata or {}).get("name"), str)
    )


def discount_field(scene):
    candidates = [
        element for element in matches(scene, kind="edit")
        if (element.label or "").strip().rstrip(":").casefold() in _DISCOUNT_LABELS
        and (element.metadata or {}).get("automation_id")
        and (element.metadata or {}).get("uia_runtime_id")
    ]
    # A form-level caption inherited by several edits cannot identify a field.
    return candidates[0] if len(candidates) == 1 else None


def discount_is_18(value):
    return isinstance(value, str) and _DISCOUNT_TEXT.fullmatch(value.strip()) is not None


def read_discount(scene, offer, api):
    if not owned_discount(scene, offer, api):
        return None
    field = discount_field(scene)
    if field is None:
        return None
    wrapper = resolve_native_wrapper(
        scene, kind="edit", label=field.label, automation_id=field.metadata["automation_id"],
        allowed_stages=("windowhub_unmapped",),
    )
    return wrapper.iface_value


def refresh_transition(loop, offer, api, destinations, *, include_discount=False):
    for attempt in range(7):
        current = inspect(loop)
        if stage_of(current) in destinations and belongs_to_offer(current, offer, api):
            return current
        if include_discount and owned_discount(current, offer, api):
            return current
        if attempt < 6:
            time.sleep(0.4)
    return None


def invoke_confirmation(scene, labels, *, still_owned):
    """One UIA Invoke, binding the unique affirmative button again before input."""
    buttons = [
        button for button in matches(scene, kind="button")
        if (button.label or "").strip().casefold() in labels
        and (button.metadata or {}).get("automation_id")
    ]
    if len(buttons) != 1:
        return False
    button = buttons[0]
    wrapper = resolve_native_wrapper(
        scene, label=button.label, automation_id=button.metadata["automation_id"],
        allowed_stages=(stage_of(scene),),
    )
    if not still_owned():
        return False
    wrapper.iface_invoke.Invoke()
    return True


def ask_ready(instruction, *, ask=None):
    try:
        answer = (ask or input)(instruction + " Wpisz 'gotowe' (Enter = przerwij): ")
    except (EOFError, KeyboardInterrupt):
        return False
    if answer.strip().casefold() != "gotowe":
        return False
    print("Wróć do WindowHub. Odczyt za 6 sekund.", flush=True)
    time.sleep(6)
    return True


def complete_discount(loop, scene, offer, api):
    if not owned_discount(scene, offer, api):
        return None
    confirmation_attempted = False
    value_verified = False
    try:
        pattern = read_discount(scene, offer, api)
        if pattern is not None:
            if not discount_is_18(pattern.CurrentValue) and not pattern.CurrentIsReadOnly:
                if owned_discount(scene, offer, api):
                    pattern.SetValue("18")
            fresh = inspect(loop)
            pattern = read_discount(fresh, offer, api)
            if pattern is not None and discount_is_18(pattern.CurrentValue):
                value_verified = True
                print("TWO_POSITION_DISCOUNT_READBACK=18")
                confirmation_attempted = invoke_confirmation(
                    fresh, {"ok", "zatwierdź", "zatwierdz"},
                    still_owned=lambda: owned_discount(fresh, offer, api),
                )
    except Exception as exc:
        print("TWO_POSITION_DISCOUNT_NATIVE=" + type(exc).__name__)
        confirmation_attempted = True
    if confirmation_attempted:
        after = refresh_transition(loop, offer, api, {"offer_document", "position"})
        if after is not None:
            print("TWO_POSITION_DISCOUNT_TRANSITION=" + stage_of(after))
            # An exception can leave the effect unknown. Require affirmative 18% evidence.
            if value_verified:
                return after

    if not ask_ready(
        "Sprawdź arkusz Rabat między pozycjami. Jeśli nadal jest otwarty, ustaw 18% "
        "i potwierdź. Wpisz „gotowe” po sprawdzeniu, że potwierdzono 18%."
    ):
        return None
    after = refresh_transition(loop, offer, api, {"offer_document", "position"})
    if after is not None:
        print("TWO_POSITION_DISCOUNT_OPERATOR_CONFIRMED=18")
    return after


def build_and_confirm(loop, offer, api, position, index):
    scene = inspect(loop)
    if stage_of(scene) != "modifier" or not belongs_to_offer(scene, offer, api):
        return None
    # The legacy visual executor cannot read exact openings or tell a fixed
    # mullion from a movable one. Keep the editor open for the operator.
    scene = handoff_scene(
        loop, offer, api, {"modifier"},
        f"Pozycja {index}. Zbuduj {position.instruction()}, {position.width} × {position.height} mm. "
        "Sprawdź biały od wewnątrz, antracyt tylko na zewnątrz oraz pakiet trzyszybowy "
        "(jeśli kreator pominął szklenie, wybierz pakiet w edytorze). "
        "Zostaw gotową konstrukcję w otwartym Modyfikatorze.",
        ask=input,
    )
    if scene is None:
        return None
    print(f"TWO_POSITION_CONSTRUCTION_OPERATOR_CONFIRMED={index}")
    try:
        attempted = invoke_confirmation(
            scene, {"ok", "zakończ", "zakoncz"},
            still_owned=lambda: belongs_to_offer(scene, offer, api),
        )
    except Exception as exc:
        print("TWO_POSITION_EDITOR_CONFIRM=" + type(exc).__name__)
        attempted = True
    destinations = {"offer_document"}
    if index == 1:
        destinations.add("position")
    if attempted:
        after = refresh_transition(loop, offer, api, destinations, include_discount=index == 1)
        if after is not None:
            return after
    if not ask_ready(
        "Jeżeli edytor jest nadal otwarty, potwierdź gotową konstrukcję. "
        "Gdy pojawi się arkusz Rabat, zostaw go otwartego."
    ):
        return None
    return refresh_transition(loop, offer, api, destinations, include_discount=index == 1)


def open_next(loop, scene, offer, api):
    if stage_of(scene) != "offer_document" or not belongs_to_offer(scene, offer, api):
        return None
    # Add normally expects the position wizard. Re-observe even if its usual
    # postcondition fails because the discount modal intercepted the transition.
    open_verified_position(loop, scene)
    return refresh_transition(loop, offer, api, {"position"}, include_discount=True)


def run_offer(loop, offer, api, *, color_label=None):
    first, second = POSITIONS
    print("TWO_POSITION_BEGIN=1")
    if run(loop, offer, api, stop_at_editor=True, editor_first=True, strict_catalog=True,
           editor_glazing_fallback=True, width=first.width, height=first.height, color_label=color_label):
        return stop("first_wizard_unverified")
    scene = build_and_confirm(loop, offer, api, first, 1)
    if scene is None:
        return stop("first_construction_confirmation_unverified")
    add_attempted = stage_of(scene) == "offer_document"
    if add_attempted:
        scene = open_next(loop, scene, offer, api)
    if scene is None or not owned_discount(scene, offer, api):
        # Some installations may expose the discount with another caption or
        # open it after a separate action. Observe its outcome if the operator
        # assists, without dispatching Add again.
        if not ask_ready(
            "Sprawdź przejście do drugiej pozycji. Jeśli jest arkusz Rabat, potwierdź 18%. "
            "Zostaw otwarty kreator drugiej pozycji. Potwierdź tylko, jeśli widziałeś ustawione 18%."
        ):
            return stop("discount_sheet_unverified")
        scene = refresh_transition(loop, offer, api, {"position"})
        if scene is None:
            return stop("second_position_entry_unverified")
        print("TWO_POSITION_DISCOUNT_OPERATOR_CONFIRMED=18")
    else:
        scene = complete_discount(loop, scene, offer, api)
        if scene is not None and stage_of(scene) == "offer_document":
            if not add_attempted:
                scene = open_next(loop, scene, offer, api)
            else:
                scene = handoff_scene(
                    loop, offer, api, {"position"},
                    "Po zatwierdzeniu rabatu WindowHub wrócił do oferty. Otwórz drugą pozycję "
                    "i pozostaw kreator „Dodawanie nowej pozycji” otwarty.",
                    ask=input,
                )
        if scene is None or stage_of(scene) != "position" or not belongs_to_offer(scene, offer, api):
            return stop("discount_or_second_position_unverified")
    print("TWO_POSITION_BEGIN=2")
    if run(loop, offer, api, stop_at_editor=True, editor_first=True, strict_catalog=True,
           editor_glazing_fallback=True, width=second.width, height=second.height, color_label=color_label):
        return stop("second_wizard_unverified")
    if build_and_confirm(loop, offer, api, second, 2) is None:
        return stop("second_construction_confirmation_unverified")
    if not ask_ready(
        "W otwartej ofercie testowej sprawdź, czy są dokładnie dwie pozycje po jednej sztuce "
        "oraz czy rabat 18% został zastosowany w wycenie. Zostaw ofertę na ekranie."
    ):
        return stop("offer_positions_not_confirmed")
    if not refresh_transition(loop, offer, api, {"offer_document"}):
        return stop("final_offer_identity_unverified")
    print("TWO_POSITION_RESULT=operator_verified_open_test_offer")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--color-label", help="Dokładna etykieta antracytu zewnętrznego i białego wnętrza")
    parser.add_argument("--start-delay", type=int, choices=range(0, 31), default=12, metavar="0..30")
    args = parser.parse_args(argv)
    if os.name != "nt" or not args.execute_live or any(
        os.environ.get(name) != "1" for name in ("COMPUTER_USE_LIVE", "WH_REAL_WINDOWHUB")
    ):
        return stop("windows_and_explicit_live_test_required")
    try:
        customer = input("Nazwa istniejącego klienta testowego: ").strip()
    except (EOFError, KeyboardInterrupt):
        return stop("no_test_customer_provided")
    if not customer or len(customer) > 100 or any(ord(char) < 32 for char in customer):
        return stop("invalid_test_customer")
    print(f"Przejdź do WindowHub. Start za {args.start_delay} s.", flush=True)
    time.sleep(args.start_delay)
    from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
    return run_from_start(
        create_windows_desktop_agent_control_loop(), customer, _Win32Mdi(),
        on_offer_ready=lambda loop, offer, api: run_offer(loop, offer, api, color_label=args.color_label),
    )


if __name__ == "__main__":
    raise SystemExit(main())
