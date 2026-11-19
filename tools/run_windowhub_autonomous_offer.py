"""Build a test offer using WindowHub's in-document drawing workspace."""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import os
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.runtime.windowhub_mdi_native_probe import _Win32Mdi
from app.agent.runtime.windowhub_new_offer_handoff import (
    NewOfferHandoff, _draft_name, active_mdi_child, active_native_draft_name, foreground_handle, owner_chain, scoped_position_stage,
)
from app.agent.runtime.windowhub_pricing_dialog import (
    PRICING_TITLE, confirm_position_pricing, parse_discount,
)
from app.agent.offers.windowhub_salesperson_policy import OfferProgress, PositionResult, PositionStatus
from app.gui.enums.gui_tool import GuiTool
from tools.run_windowhub_existing_offer_position_test import (
    belongs_to_offer, inspect, run, run_from_start,
)
from tools.run_windowhub_two_position_live import (
    invoke_confirmation, open_next, owned_discount, refresh_transition,
)

STEPS = {
    "empty": (GuiTool.FRAME, "frame"),
    "frame": (GuiTool.GLASS, "fixed_glazed"),
}
POSITIONS = ((1000, 1000), (1100, 1000))


class WorkspaceBlocked(RuntimeError):
    pass


def capture(loop, offer, api):
    from app.wh.vision.mss_screenshot_engine import MSSScreenshotEngine

    scene = inspect(loop)
    if scoped_position_stage(scene, offer, api) != "offer_document" or not belongs_to_offer(scene, offer, api):
        raise WorkspaceBlocked("active_offer_workspace_unverified:" + str(stage_of(scene)))
    meta = scene.observation.metadata
    rect = meta.get("window_rect")
    if rect is None or min(rect.width, rect.height) <= 0:
        raise WorkspaceBlocked("active_window_bounds_missing")
    shot = MSSScreenshotEngine().capture(rect)
    if not owns_native_workspace(scene, offer, api):
        raise WorkspaceBlocked("active_offer_changed_during_capture")
    rgb = shot.image[:, :, 2::-1].copy()
    check = offer.visual_draft_check if isinstance(offer, NewOfferHandoff) else None
    if check is not None and not check(rgb):
        raise WorkspaceBlocked("visual_draft_tab_changed")
    return scene, rect, rgb


def read_position_drawing(rgb, number, size):
    import cv2
    from app.agent.learning.windowhub_offer_editor import (
        locate_drawing, selected_row_box, selected_window_matches,
    )
    from app.agent.offers.windowhub_customer_visual_selection import _ocr_text_results

    row = selected_row_box(rgb)
    if row is None:
        raise WorkspaceBlocked("selected_position_row_unverified")
    gray = cv2.cvtColor(row.crop(rgb), cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(255 - gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    if not selected_window_matches(_ocr_text_results(gray, (0, 0)), number, *size):
        raise WorkspaceBlocked("selected_window_number_quantity_or_dimensions_unverified")
    drawing, evidence = locate_drawing(rgb, row, expected_size=size)
    if evidence["diagnosis"] != "primary":
        print("WH_RECOVERY_DRAWING=" + json.dumps(evidence, sort_keys=True), flush=True)
    if drawing is None:
        raise WorkspaceBlocked("drawing_outline_unverified:" + evidence["diagnosis"])
    return drawing


def observe_workspace(loop, offer, api, number, size, *, opening=False):
    from app.agent.learning.windowhub_offer_editor import fixed_window_stage

    scene, rect, rgb = capture(loop, offer, api)
    drawing = read_position_drawing(rgb, number, size)
    if opening:
        from app.agent.learning.windowhub_builder_replay import observe_builder_stage
        state = observe_builder_stage(drawing.crop(rgb))
    else:
        state = fixed_window_stage(drawing.crop(rgb))
    return scene, rect, rgb, drawing, state


def native_glazing_target(hwnd, toolbars, api):
    """Resolve a named enabled glazing button in the current toolbar."""
    from pywinauto import Desktop

    root = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
    controls = []
    for button in root.descendants(control_type="Button"):
        try:
            info = button.element_info
            name = " ".join((info.name or "").casefold().split())
            if name not in {"wstawianie szklenia", "wstaw szklenie", "wstawianie szkleń"} or not info.visible:
                continue
            current = button
            for _ in range(12):
                if current is None:
                    break
                handle = current.element_info.handle
                if handle in toolbars and api.parent(handle, 2) == hwnd:
                    controls.append((handle, button))
                    break
                current = current.parent()
        except Exception:
            continue
    if not controls:
        return None
    if len(controls) != 1 or not controls[0][1].element_info.enabled:
        raise WorkspaceBlocked("glazing_native_control_ambiguous_or_disabled")
    handle, button = controls[0]
    r = button.rectangle()
    if r.right <= r.left or r.bottom <= r.top:
        raise WorkspaceBlocked("construction_tool_unverified:GLASS")
    return handle, ((r.left + r.right) // 2, (r.top + r.bottom) // 2)


def blue_icon_pixels(rgb):
    red, _, blue = rgb.transpose(2, 0, 1).astype("int16")
    return (blue - red).clip(0, 255).astype("uint8")


def active_glazing_icon(colors, hit):
    x, y = hit
    patch = colors[max(0, y - 5):y + 6, max(0, x - 5):x + 6]
    return bool(patch.size and (patch > 35).mean() >= 0.45)


def alternate_glazing_target(rgb, template, frame, sash):
    """Find an enabled icon in the glazing slot relative to frame and sash."""
    from app.agent.learning.windowhub_offer_editor import toolbar_tool

    if frame is None or sash is None:
        return None
    spacing = sash[1] - frame[1]
    if not 24 <= spacing <= 80 or abs(frame[0] - sash[0]) > 8:
        return None
    expected = sash[1] + 2 * spacing
    start = max(0, expected - spacing // 2 - template.shape[0] // 2)
    stop = min(rgb.shape[0], expected + spacing // 2 + template.shape[0] // 2)
    colors = blue_icon_pixels(rgb)
    hit = toolbar_tool(colors[start:stop], blue_icon_pixels(template))
    if hit is None:
        return None
    hit = (hit[0], hit[1] + start)
    if abs(hit[1] - expected) > spacing // 3 or abs(hit[0] - sash[0]) > 8:
        return None
    return hit if active_glazing_icon(colors, hit) else None


def tool_target(rgb, rect, hwnd, tool, *, api=None):
    import cv2
    import numpy as np
    from PIL import Image
    from app.agent.learning.windowhub_offer_editor import Box, toolbar_tool
    from demo.run_native_toolbar_button_probe_live import _get_window_rect
    from tools.check_windowhub_builder_sequence import ARCHIVED_TEMPLATES

    native = api if api is not None else _Win32Mdi()
    toolbars = native.visible_toolbars(hwnd)
    if not toolbars:
        raise WorkspaceBlocked("native_construction_toolbar_missing")
    def load_template(kind):
        name, scale = ARCHIVED_TEMPLATES[kind]
        with Image.open(ROOT / "templates" / name) as source:
            return np.asarray(source.convert("L").resize(
                (round(source.width * scale), round(source.height * scale)), Image.Resampling.BILINEAR,
            ))

    alternate = None
    if tool is GuiTool.GLASS:
        try:
            target = native_glazing_target(hwnd, toolbars, native)
        except WorkspaceBlocked:
            raise
        except Exception as exc:
            print("WH_GLAZING_NATIVE=" + type(exc).__name__, flush=True)
            target = None
        if target is not None:
            toolbar, (x, y) = target
            print("WH_RECOVERY_GLAZING=verified_native_label", flush=True)
            return toolbar, (x - rect.left, y - rect.top)
        with Image.open(ROOT / "dataset_archive/glass_tool/glass_tool.png") as source:
            alternate = np.asarray(source.convert("RGB").resize((33, 33), Image.Resampling.BILINEAR))
        frame_template = load_template(GuiTool.FRAME)
        sash_template = load_template(GuiTool.SASH)

    template = load_template(tool)
    targets = []
    for toolbar in toolbars:
        x, y, width, height = _get_window_rect(toolbar)
        bounds = Box(x - rect.left, y - rect.top, width, height)
        if (
            bounds.x < 0 or bounds.y < 0 or bounds.right > rgb.shape[1]
            or bounds.bottom > rgb.shape[0] or height <= 2 * width or width <= 0
        ):
            continue
        pixels = bounds.crop(rgb)
        gray = cv2.cvtColor(pixels, cv2.COLOR_RGB2GRAY)
        hit = toolbar_tool(gray, template)
        if alternate is not None and (hit is None or not active_glazing_icon(blue_icon_pixels(pixels), hit)):
            hit = alternate_glazing_target(
                pixels, alternate, toolbar_tool(gray, frame_template), toolbar_tool(gray, sash_template),
            )
            if hit is not None:
                print("WH_RECOVERY_GLAZING=verified_active_icon_variant", flush=True)
        if hit is not None:
            targets.append((toolbar, (bounds.x + hit[0], bounds.y + hit[1])))
    if len(targets) != 1:
        raise WorkspaceBlocked("construction_tool_unverified:" + tool.name)
    return targets[0]


def verify_editor_transition(scene, offer, api, number, size, *, opening, blank=False):
    """Observe the wizard destination with the same vision that drives building."""
    from app.agent.learning.windowhub_builder_replay import NEXT_STEP, observe_builder_stage
    from app.agent.learning.windowhub_offer_editor import fixed_window_stage
    from app.wh.vision.mss_screenshot_engine import MSSScreenshotEngine

    scope = offer.editor_candidate(scene, api, observed_replacement=True)
    if scope != "eligible":
        print("WH_EDITOR_EVIDENCE=" + scope, flush=True)
        return False
    child = active_mdi_child(offer.frame, api)
    rect = scene.observation.metadata.get("window_rect")
    if rect is None or min(rect.width, rect.height) <= 0:
        print("WH_EDITOR_EVIDENCE=no_workspace_bounds", flush=True)
        return False
    try:
        image = MSSScreenshotEngine().capture(rect).image[:, :, 2::-1].copy()
        check = getattr(offer, "visual_draft_check", None)
        if check is not None and not check(image):
            raise WorkspaceBlocked("visual_draft_tab_changed")
        drawing = read_position_drawing(image, number, size)
        classify = observe_builder_stage if opening else fixed_window_stage
        state = classify(drawing.crop(image))
        allowed = {"empty", "frame", "sash", "glass", "opening_marker"} if opening else {"empty", "frame", "fixed_glazed"}
        if state not in ({"empty"} if blank else allowed):
            raise WorkspaceBlocked("unexpected_initial_drawing:" + state)
        step = (NEXT_STEP if opening else STEPS).get(state)
        if not blank and step is not None:
            tool_target(image, rect, offer.frame, step[0], api=api)
    except (WorkspaceBlocked, OSError, RuntimeError, ValueError) as exc:
        reason = str(exc) if isinstance(exc, WorkspaceBlocked) else type(exc).__name__
        print("WH_EDITOR_EVIDENCE=" + reason, flush=True)
        print("WH_RECOVERY_NEXT=" + recovery_advice(reason), flush=True)
        return False
    verified = bool(child and active_mdi_child(offer.frame, api) == child and offer.accept_visual_editor(scene, api))
    print("WH_EDITOR_EVIDENCE=" + ("verified_" + state if verified else "workspace_changed"), flush=True)
    return verified


def owns_native_workspace(scene, offer, api):
    from app.agent.runtime.windowhub_mdi_native_probe import same_offer_id

    hwnd = scene.observation.metadata.get("window_handle")
    if not belongs_to_offer(scene, offer, api):
        return False
    if isinstance(offer, NewOfferHandoff):
        return hwnd == offer.frame
    live_title = api.title(hwnd).strip()
    return live_title.casefold().startswith("okna - ofr/") and same_offer_id(live_title[7:], offer)


def click_owned(scene, rect, offer, api, point, *, toolbar=None):
    import ctypes
    from ctypes import wintypes
    from app.runtime.execution.mouse_controller import MouseController

    if not (0 <= point[0] < rect.width and 0 <= point[1] < rect.height):
        raise WorkspaceBlocked("point_outside_foreground_offer")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    hit_test = user32.WindowFromPoint
    hit_test.argtypes = [wintypes.POINT]
    hit_test.restype = wintypes.HWND
    x, y = rect.left + point[0], rect.top + point[1]
    hit = hit_test(wintypes.POINT(x, y))
    hwnd = scene.observation.metadata["window_handle"]
    if (
        not hit or api.parent(hit, 2) != hwnd
        or (toolbar is not None and hit != toolbar)
        or not owns_native_workspace(scene, offer, api)
    ):
        raise WorkspaceBlocked("native_input_target_changed")
    MouseController().click(x, y)


def apply_ur_hardware(loop, api, frame, child):
    import re
    from app.agent.runtime.windowhub_hardware_dialog import choose_and_confirm_ur

    for attempt in range(8):
        scene = inspect(loop)
        hwnd = foreground_handle(scene, api)

        def still_owned():
            return (
                hwnd and hwnd != frame and child and api.foreground() == hwnd
                and api.pid(hwnd) == api.pid(frame) and active_mdi_child(frame, api) == child
                and (frame in owner_chain(hwnd, api) or api.parent(hwnd, 3) == frame)
                and bool(re.fullmatch(r"wybór okuć(?:\s*:\s*\d+)?", api.title(hwnd).strip(), re.IGNORECASE))
            )

        if still_owned():
            try:
                applied = choose_and_confirm_ur(
                    hwnd, still_owned=still_owned,
                    confirm=lambda: invoke_confirmation(scene, {"ok"}, still_owned=still_owned),
                )
            except Exception as exc:
                raise WorkspaceBlocked("hardware_catalog_" + type(exc).__name__) from exc
            if applied:
                return
            raise WorkspaceBlocked("compatible_ur_option_or_confirmation_unverified")
        if attempt < 7:
            time.sleep(0.25)
    raise WorkspaceBlocked("owned_hardware_dialog_not_observed")


def recovery_advice(reason):
    code = reason.split(":", 1)[0]
    if code.startswith("pricing_"):
        return "Sprawdź rabat i wycenę bieżącej pozycji. Potwierdź wycenę ręcznie, jeśli agent nie mógł jej odczytać."
    if code == "next_position_dialog_requires_review":
        return "Sprawdź dialog otwarty przez Dodaj, np. wycenę. Zatwierdź go po sprawdzeniu warunków."
    if code in {"draft_add_control_unverified", "next_position_transition_unverified"}:
        return "Sprawdź przycisk Dodaj w tej samej pozycji oraz czy WindowHub otworzył kreator."
    if code in {"drawing_outline_unverified", "new_position_unverified"}:
        return "Odsłoń pole rysunku pod tabelą i sprawdź, czy widać cały obrys bieżącej pozycji."
    if code in {"selected_position_row_unverified", "selected_window_number_quantity_or_dimensions_unverified"}:
        return "Zaznacz w szkicu właściwy wiersz i sprawdź numer pozycji, ilość i wymiary z polecenia."
    if code == "glazing_native_control_ambiguous_or_disabled":
        return "Sprawdź, czy WindowHub udostępnił aktywne narzędzie Wstawianie szklenia po wybraniu skrzydła."
    if code in {"construction_tool_unverified", "native_construction_toolbar_missing"}:
        return "Odsłoń pasek Narzędzia edytora i sprawdź, czy ikona bieżącej operacji jest dostępna."
    if code in {"compatible_ur_option_or_confirmation_unverified", "owned_hardware_dialog_not_observed"}:
        return "Sprawdź, czy otworzył się dobór okuć i czy katalog udostępnia jednoznaczny wariant UR."
    if code in {"drawing_changed_after_tool_selection", "construction_effect_unverified"}:
        return "Sprawdź rysunek i ewentualny dialog WindowHub. Potwierdź efekt przed ponownym wykonaniem czynności."
    if code in {"active_offer_workspace_unverified", "active_offer_changed_during_capture",
                "native_input_target_changed", "requested_editor_draft_not_selected", "visual_draft_tab_changed"}:
        return "Przywróć na pierwszy plan właściwy szkic i zaznacz pozycję wskazaną w poleceniu."
    return "Sprawdź ostatni komunikat WindowHub i stan bieżącej pozycji."


def effect_evidence(before, after, tool, expected, blocked):
    observed = after[-1] if after is not None else None
    pixel_change = None
    if after is not None and before[2] is not None and after[2] is not None:
        import numpy as np

        initial = before[3].crop(before[2])
        final = after[3].crop(after[2])
        if initial.shape == final.shape:
            pixel_change = round(float(np.any(initial != final, axis=-1).mean()), 4)
    return {
        "action": tool.name, "before": before[-1], "expected": expected, "observed": observed,
        "fraction_pixels_changed": pixel_change, "blocked": blocked,
    }


def build_fixed(loop, offer, api, number, size):
    return build_construction(loop, offer, api, number, size)


def build_construction(loop, offer, api, number, size, *, opening=False):
    from app.agent.knowledge.whokna_offer_guide import single_sash_construction_recipe

    try:
        recipe = single_sash_construction_recipe() if opening else None
    except (KeyError, OSError, ValueError) as exc:
        raise WorkspaceBlocked("construction_reference_incomplete") from exc
    steps = recipe if opening else STEPS

    def observe():
        if opening:
            return observe_workspace(loop, offer, api, number, size, opening=True)
        return observe_workspace(loop, offer, api, number, size)

    current = observe()
    fresh_draft = isinstance(offer, NewOfferHandoff) and offer.visual_editor_child
    complete = "opening_marker" if opening else "fixed_glazed"
    initial_states = {*steps, complete} if fresh_draft else {"empty"}
    if current[-1] not in initial_states:
        raise WorkspaceBlocked("new_position_unverified:" + current[-1])
    if current[-1] != "empty":
        print("WH_RESUME_DRAWING=" + current[-1], flush=True)
    for _ in steps:
        if current[-1] == complete:
            return current[0]
        scene, rect, rgb, drawing, stage = current
        if recipe:
            tool, expected, source_rules = recipe[stage]
            print("WH_PLAN_RULES=" + ",".join(rule["id"] for rule in source_rules), flush=True)
        else:
            tool, expected = steps[stage]
        hwnd = scene.observation.metadata["window_handle"]
        toolbar, target = tool_target(rgb, rect, hwnd, tool)
        print(f"WH_AUTONOMOUS_ACTION={number}:{tool.name}", flush=True)
        click_owned(scene, rect, offer, api, target, toolbar=toolbar)
        # A toolbar click can alter the selected document, the visible row or
        # the canvas geometry. Authorize placement only after a fresh read.
        before = observe()
        active, active_rect, _, active_drawing, active_stage = before
        if active_stage != stage or active.observation.metadata["window_handle"] != hwnd:
            raise WorkspaceBlocked("drawing_changed_after_tool_selection")
        hardware_child = active_mdi_child(hwnd, api) if tool is GuiTool.HARDWARE else None
        if tool is GuiTool.HARDWARE and not hardware_child:
            raise WorkspaceBlocked("hardware_document_scope_unverified")
        click_owned(active, active_rect, offer, api, active_drawing.center)
        if tool is GuiTool.HARDWARE:
            apply_ur_hardware(loop, api, hwnd, hardware_child)
        last_observation = None
        blocked = None
        for attempt in range(5):
            try:
                after = observe()
                last_observation, blocked = after, None
            except WorkspaceBlocked as exc:
                last_observation, blocked = None, str(exc)
            else:
                frame_and_sash = opening and tool is GuiTool.FRAME and after[-1] == "sash"
                if after[-1] == expected or frame_and_sash:
                    current = after
                    if attempt:
                        print(f"WH_RECOVERY=effect_verified_after_{attempt + 1}_reads", flush=True)
                    print(f"WH_AUTONOMOUS_VERIFIED={number}:{'frame_and_sash' if frame_and_sash else expected}", flush=True)
                    if expected == "opening_marker":
                        from app.agent.learning.windowhub_opening_marker import read_opening_marker_side
                        direction = read_opening_marker_side(current[3].crop(current[2]))
                        print(f"WH_AUTONOMOUS_OPENING_MARKER={direction}", flush=True)
                    break
            if attempt < 4:
                time.sleep(0.25)
        else:
            evidence = effect_evidence(before, last_observation, tool, expected, blocked)
            print("WH_RECOVERY_EFFECT=" + json.dumps(evidence, sort_keys=True), flush=True)
            raise WorkspaceBlocked("construction_effect_unverified:" + (blocked or str(evidence["observed"])))
    if current[-1] != complete:
        raise WorkspaceBlocked("construction_postcondition_unverified:" + current[-1])
    return current[0]


def finish_position(loop, offer, api, number, size, *, opening, blank, progress):
    if blank:
        _, _, _, _, state = observe_workspace(loop, offer, api, number, size, opening=opening)
        if state != "empty":
            raise WorkspaceBlocked(f"placeholder_not_empty:{number}")
        result = PositionResult(
            number, PositionStatus.PARTIAL, dimensions_verified=True, draft_placeholder_verified=True,
            missing=("configuration_requires_clarification",),
        )
        print(f"WH_POSITION_PLACEHOLDER_VERIFIED={number}", flush=True)
    else:
        if opening:
            build_construction(loop, offer, api, number, size, opening=True)
        else:
            build_fixed(loop, offer, api, number, size)
        result = PositionResult(number, PositionStatus.COMPLETE, dimensions_verified=True, complete_verified=True)
    if progress is not None:
        progress.record(result)


def run_offer(
    loop, offer, api, positions, *, construction="fix", discount=Decimal(0), leave_blank=(), progress=None,
):
    opening = construction == "ur"
    for number, size in enumerate(positions, 1):
        if number > 1:
            if isinstance(offer, NewOfferHandoff):
                scene = open_draft_next_position(
                    loop, offer, api, number - 1, positions[number - 2], opening=construction == "ur",
                    discount=discount, blank=number - 1 in leave_blank,
                )
                if not offer.bind_next_position(scene, api):
                    raise WorkspaceBlocked("next_position_wizard_scope_unverified")
            else:
                predecessor = inspect(loop)
                scene = open_next(loop, predecessor, offer, api, include_pricing=True)
                if scene is not None and owned_discount(scene, offer, api, include_pricing=True):
                    hwnd = foreground_handle(scene, api)

                    def still_owned():
                        return api.title(hwnd).strip().casefold() == PRICING_TITLE and owned_discount(scene, offer, api, include_pricing=True)

                    if not apply_position_pricing(hwnd, discount, still_owned):
                        raise WorkspaceBlocked("pricing_discount_or_confirmation_unverified")
                    scene = refresh_transition(loop, offer, api, {"position"})
                    if scene is not None:
                        print("WH_PRICING_TRANSITION=position", flush=True)
                if scene is None or stage_of(scene) != "position" or not belongs_to_offer(scene, offer, api):
                    raise WorkspaceBlocked("next_position_or_discount_unverified")
        print(f"WH_AUTONOMOUS_POSITION={number}:{size[0]}x{size[1]}", flush=True)
        status = run(
            loop, offer, api, stop_at_editor=True, width=size[0], height=size[1],
            allow_offer_workspace=True, editor_glazing_fallback=True,
            verify_editor=lambda scene, scope, api: verify_editor_transition(
                scene, scope, api, number, size, opening=opening, blank=number in leave_blank,
            ),
        )
        if status:
            raise WorkspaceBlocked(f"position_wizard_unverified:{number}")
        if isinstance(offer, NewOfferHandoff):
            workspace = inspect(loop)
            if scoped_position_stage(workspace, offer, api) != "offer_document" or not belongs_to_offer(workspace, offer, api):
                raise WorkspaceBlocked("workspace_after_wizard_unverified:" + str(stage_of(workspace)))
        finish_position(loop, offer, api, number, size,
                        opening=opening, blank=number in leave_blank, progress=progress)
    print(f"WH_AUTONOMOUS_RESULT=verified_draft_positions:{len(positions) - len(leave_blank)}", flush=True)
    print("WH_AUTONOMOUS_PRICE_AND_SAVE=not_verified", flush=True)
    return 0


def observe_selected_draft_tab(scene, api, name=None):
    """Read only the visually selected tab and retain its image for rechecks."""
    from app.wh.vision.mss_screenshot_engine import MSSScreenshotEngine

    frame = foreground_handle(scene, api)
    rect = scene.observation.metadata.get("window_rect")
    if not frame or stage_of(scene) != "windowhub_unmapped" or rect is None:
        print("WH_DRAFT_EVIDENCE=foreground_editor_unverified", flush=True)
        return None
    child = active_mdi_child(frame, api)
    if not child or api.pid(frame) != api.pid(child):
        print("WH_DRAFT_EVIDENCE=active_native_document_unverified", flush=True)
        return None
    image = MSSScreenshotEngine().capture(rect).image[:, :, 2::-1].copy()
    visual = read_visual_draft_tab(image, name)
    if visual is None or foreground_handle(scene, api) != frame or active_mdi_child(frame, api) != child:
        return None
    observed_name, _, check = visual
    return observed_name, check


def read_visual_draft_tab(image, name=None):
    import cv2
    import numpy as np
    from app.agent.learning.windowhub_offer_editor import selected_tab_crop_box
    from app.agent.offers.windowhub_customer_visual_selection import _ocr_text_results

    box = selected_tab_crop_box(image)
    if box is None:
        print("WH_DRAFT_EVIDENCE=active_tab_shape_unverified", flush=True)
        return None
    crop = box.crop(image)
    label = crop[:, 2 * box.height:]
    if label.shape[1] < 25:
        print("WH_DRAFT_EVIDENCE=active_tab_name_unverified", flush=True)
        return None
    gray = cv2.resize(cv2.cvtColor(label, cv2.COLOR_RGB2GRAY), None, fx=4, fy=4)
    binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)[1]
    binary = cv2.copyMakeBorder(binary, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=255)

    def normalize(value):
        return re.sub(r"[\s*]+", "", value).casefold()
    names = [
        normalize(line.label) for line in (_ocr_text_results(binary, (0, 0)) or ())
        if line.confidence >= 0.85 and re.fullmatch(r"dokument\s*\d+\s*\*?", line.label.strip(), re.IGNORECASE)
    ]
    if len(names) != 1:
        print("WH_DRAFT_EVIDENCE=active_tab_name_unverified", flush=True)
        return None
    observed_name = names[0]
    print("WH_DRAFT_OBSERVED=" + observed_name, flush=True)
    if name is not None and observed_name != normalize(name):
        print("WH_DRAFT_EVIDENCE=different_active_draft", flush=True)
        return None
    def check(rgb):
        return selected_tab_crop_box(rgb) == box and np.array_equal(box.crop(rgb), crop)

    print("WH_DRAFT_EVIDENCE=verified_visual_active_tab", flush=True)
    return observed_name, box, check


def find_draft_add_button(frame, child, api):
    from pywinauto import Desktop
    from app.agent.runtime.windowhub_mdi_native_probe import _win32_mdi_lineage

    candidates = []
    for wrapper in Desktop(backend="uia").window(handle=frame).wrapper_object().descendants(control_type="Button"):
        try:
            info = wrapper.element_info
            if (info.name or "").strip().casefold() != "dodaj" or not info.visible or not info.enabled:
                continue
            lineage = _win32_mdi_lineage(wrapper, api)
            if lineage is not None and lineage[1] == child:
                candidates.append(wrapper)
        except Exception:
            continue
    return candidates[0] if len(candidates) == 1 else None


def apply_position_pricing(hwnd, discount, still_owned):
    try:
        return confirm_position_pricing(hwnd, discount, still_owned=still_owned)
    except Exception as exc:
        # A native exception can occur after invoking the button. Never retry.
        print("WH_PRICING_ACTION_UNCERTAIN=" + type(exc).__name__, flush=True)
        return False


def owned_draft_dialog(hwnd, offer, api):
    return bool(
        hwnd and hwnd != offer.frame and api.foreground() == hwnd and api.pid(hwnd) == offer.pid
        and api.pid(offer.frame) == offer.pid and api.pid(offer.child) == offer.pid
        and active_mdi_child(offer.frame, api) == offer.child
        and (offer.frame in owner_chain(hwnd, api) or api.parent(hwnd, 3) == offer.frame)
    )


def wait_for_next_wizard(loop, offer, api, discount, *, accepted_hwnd=0):
    for attempt in range(12):
        after = inspect(loop)
        hwnd = foreground_handle(after, api)
        if not hwnd or api.pid(hwnd) != offer.pid or active_mdi_child(offer.frame, api) != offer.child:
            raise WorkspaceBlocked("next_position_document_changed")
        if hwnd != offer.frame:
            if not owned_draft_dialog(hwnd, offer, api):
                raise WorkspaceBlocked("next_position_dialog_unowned")
            if stage_of(after) == "position":
                if accepted_hwnd:
                    print("WH_PRICING_TRANSITION=position", flush=True)
                print("WH_NEXT_POSITION=wizard_open", flush=True)
                return after
            title = api.title(hwnd).strip().casefold()
            if title != PRICING_TITLE:
                raise WorkspaceBlocked("next_position_dialog_requires_review")
            if accepted_hwnd and hwnd != accepted_hwnd:
                raise WorkspaceBlocked("pricing_second_dialog_requires_review")
            if not accepted_hwnd:
                if not apply_position_pricing(hwnd, discount, lambda: (
                    owned_draft_dialog(hwnd, offer, api) and api.title(hwnd).strip().casefold() == PRICING_TITLE
                )):
                    raise WorkspaceBlocked("pricing_discount_or_confirmation_unverified")
                accepted_hwnd = hwnd
        if attempt < 11:
            time.sleep(0.25)
    raise WorkspaceBlocked("pricing_transition_unverified" if accepted_hwnd else "next_position_transition_unverified")


def open_draft_next_position(loop, offer, api, number, size, *, opening, discount=Decimal(0), blank=False):
    complete = "empty" if blank else ("opening_marker" if opening else "fixed_glazed")
    scene, rect, _, _, observed = observe_workspace(loop, offer, api, number, size, opening=opening)
    if observed != complete:
        raise WorkspaceBlocked("next_position_previous_construction_unverified")

    try:
        button = find_draft_add_button(offer.frame, offer.child, api)
    except Exception as exc:
        raise WorkspaceBlocked("draft_add_control_unverified") from exc
    if button is None or not owns_native_workspace(scene, offer, api):
        raise WorkspaceBlocked("draft_add_control_unverified")

    try:
        invoke = button.iface_invoke
    except Exception:
        invoke = None
    if invoke is not None:
        invoke.Invoke()
    else:
        bounds = button.rectangle()
        point = ((bounds.left + bounds.right) // 2 - rect.left, (bounds.top + bounds.bottom) // 2 - rect.top)
        click_owned(scene, rect, offer, api, point)
    print("WH_NEXT_POSITION_ACTION=add", flush=True)

    return wait_for_next_wizard(loop, offer, api, discount)


def build_selected_draft(
    loop, api, name, size, *, construction, next_position=False, next_size=None, discount=Decimal(0),
    leave_blank=(), progress=None,
):
    scene = inspect(loop)
    take_active_draft = name.casefold() == "active"
    requested = None if take_active_draft else name
    bound_name = active_native_draft_name(scene, api) if take_active_draft else requested
    scope = NewOfferHandoff.bind_selected_draft(scene, api, bound_name) if bound_name else None
    if scope is None:
        visual = observe_selected_draft_tab(scene, api, requested)
        if visual is not None:
            bound_name, check = visual
            scope = NewOfferHandoff.bind_selected_draft(scene, api, bound_name, visual_draft_check=check)
            if scope is None:
                print("WH_DRAFT_EVIDENCE=native_tab_conflicts_with_visual_name", flush=True)
    if scope is None:
        raise WorkspaceBlocked("requested_editor_draft_not_selected")
    print("WH_DRAFT_TARGET=" + bound_name, flush=True)
    opening = construction == "ur"
    if not verify_editor_transition(scene, scope, api, 1, size, opening=opening, blank=1 in leave_blank):
        raise WorkspaceBlocked("selected_editor_draft_not_verified")
    finish_position(loop, scope, api, 1, size, opening=opening, blank=1 in leave_blank, progress=progress)
    if next_size is None:
        print(f"WH_AUTONOMOUS_RESULT=verified_draft_positions:{int(1 not in leave_blank)}", flush=True)
        if next_position:
            open_draft_next_position(loop, scope, api, 1, size, opening=opening, discount=discount, blank=1 in leave_blank)
    else:
        print("WH_POSITION_COMPLETE=1", flush=True)
        wizard = open_draft_next_position(loop, scope, api, 1, size, opening=opening, discount=discount, blank=1 in leave_blank)
        if not scope.bind_next_position(wizard, api):
            raise WorkspaceBlocked("next_position_wizard_scope_unverified")
        build_next_draft_window(loop, scope, api, next_size, opening=opening, blank=2 in leave_blank, progress=progress)
        print(f"WH_AUTONOMOUS_RESULT=verified_draft_positions:{2 - len(leave_blank)}", flush=True)
    print("WH_AUTONOMOUS_PRICE_AND_SAVE=not_verified", flush=True)
    return 0


def build_next_draft_window(loop, scope, api, size, *, opening, blank=False, progress=None):
    result = run(
        loop, scope, api, stop_at_editor=True, width=size[0], height=size[1],
        allow_offer_workspace=True, editor_glazing_fallback=True,
        verify_editor=lambda scene, scope, api: verify_editor_transition(
            scene, scope, api, 2, size, opening=opening, blank=blank,
        ),
    )
    if result:
        raise WorkspaceBlocked("position_wizard_unverified:2")
    finish_position(loop, scope, api, 2, size, opening=opening, blank=blank, progress=progress)


def bind_draft_pricing(scene, api, requested):
    """Recover a native test draft identity from the owned foreground pricing dialog."""
    if stage_of(scene) != "windowhub_unmapped":
        return None
    hwnd = foreground_handle(scene, api)
    if not hwnd or api.title(hwnd).strip().casefold() != PRICING_TITLE:
        return None
    frames = set(owner_chain(hwnd, api)[1:]) | {api.parent(hwnd, 3)}
    candidates = [(frame, child) for frame in frames
                  if frame and (child := active_mdi_child(frame, api))]
    if len(candidates) != 1:
        return None
    frame, child = candidates[0]
    pid = api.pid(frame)
    if not pid:
        return None
    captions = [api.title(frame).strip(), api.title(child).strip()]
    if any(re.match(r"(?:okna - )?(?:ofr/|zlc/|start1)", value, re.I) for value in captions):
        return None
    names = {name for value in captions if (name := _draft_name(value))}
    if len(names) > 1:
        return None
    name = next(iter(names), None)
    visual_check = None
    if name is None:
        if captions[0].casefold() not in {"okna -", "okna"} or captions[1]:
            return None
        evidence = read_draft_behind_pricing(frame, hwnd, requested)
        if evidence is None:
            return None
        name, visual_check = evidence
    if requested.casefold() != "active" and _draft_name(requested) != name:
        return None
    scope = NewOfferHandoff(frame, pid, 0, frozenset(), None, child=child, explicit_draft=name,
                            visual_draft_check=visual_check)
    return scope if owned_draft_dialog(hwnd, scope, api) else None


def read_draft_behind_pricing(frame, modal, requested):
    from app.runtime.execution.window.window_rect import WindowRect
    from app.wh.vision.mss_screenshot_engine import MSSScreenshotEngine
    from pywinauto import Desktop

    desktop = Desktop(backend="win32")

    try:
        bounds = desktop.window(handle=frame).wrapper_object().rectangle()
        cover = desktop.window(handle=modal).wrapper_object().rectangle()
        rect = WindowRect(bounds.left, bounds.top, bounds.width(), bounds.height())
        image = MSSScreenshotEngine().capture(rect).image[:, :, 2::-1].copy()
        readback = read_visual_draft_tab(image, None if requested.casefold() == "active" else requested)
        if readback is None:
            return None
        name, box, check = readback
        if not uncovered_tab(box, bounds, cover):
            return None
    except (AttributeError, OSError, RuntimeError, ValueError):
        return None
    return name, check


def uncovered_tab(box, bounds, cover):
    return (
        bounds.left + box.right <= cover.left or bounds.left + box.x >= cover.right
        or bounds.top + box.bottom <= cover.top or bounds.top + box.y >= cover.bottom
    )


def resume_draft_pricing(loop, api, name, size, *, construction, discount, progress):
    scene = inspect(loop)
    scope = bind_draft_pricing(scene, api, name)
    if scope is None:
        raise WorkspaceBlocked("pricing_draft_identity_unverified")
    hwnd = foreground_handle(scene, api)

    def still_owned():
        fresh = bind_draft_pricing(scene, api, scope.explicit_draft)
        return bool(fresh and (fresh.frame, fresh.child, fresh.pid) == (scope.frame, scope.child, scope.pid))

    if not apply_position_pricing(hwnd, discount, still_owned):
        raise WorkspaceBlocked("pricing_discount_or_confirmation_unverified")
    wizard = wait_for_next_wizard(loop, scope, api, discount, accepted_hwnd=hwnd)
    if size is not None:
        if not scope.bind_next_position(wizard, api):
            raise WorkspaceBlocked("next_position_wizard_scope_unverified")
        build_next_draft_window(loop, scope, api, size, opening=construction == "ur", progress=progress)
        print("WH_AUTONOMOUS_RESULT=verified_resumed_position:2", flush=True)
    return 0


def window_size(value):
    match = re.fullmatch(r"\s*([0-9]{3,4})\s*[xX×]\s*([0-9]{3,4})\s*", value)
    if not match or not all(100 <= int(n) <= 5000 for n in match.groups()):
        raise argparse.ArgumentTypeError("podaj szerokość i wysokość w mm, np. 1200x1000")
    return tuple(map(int, match.groups()))


def discount_percentage(value):
    discount = parse_discount(value)
    if discount is None:
        raise argparse.ArgumentTypeError("podaj rabat od 0 do 100% z maksymalnie dwiema cyframi po przecinku")
    return discount


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--construction", choices=("fix", "ur"), default="fix",
                        help="Rodzaj konstrukcji. UR to jedno skrzydło rozwierno-uchylne.")
    parser.add_argument("--editor-draft", metavar="DokumentN|active",
                        help="Buduj pierwszą pozycję w podanym szkicu lub wybierz active dla zaznaczonego szkicu.")
    parser.add_argument("--next-position", action="store_true",
                        help="Po weryfikacji okna otwórz następną pozycję w tym samym szkicu.")
    parser.add_argument("--resume-pricing", action="store_true",
                        help="Wznów z otwartej wyceny szkicu. Opcjonalne --window opisuje pozycję 2.")
    parser.add_argument("--leave-blank", action="append", type=int, choices=(1, 2),
                        help="Pozostaw wskazaną pozycję bez konstrukcji, z odczytanymi wymiarami.")
    parser.add_argument("--discount", type=discount_percentage, default=Decimal(0), metavar="PROCENT",
                        help="Rabat bieżącej pozycji w arkuszu wyceny między pozycjami. Domyślnie 0%%.")
    parser.add_argument("--positions", type=int, choices=(1, 2), default=2)
    parser.add_argument("--window", action="append", type=window_size, metavar="SZERxWYS",
                        help="Wymiary okna w mm. Powtórz opcję dla drugiej pozycji.")
    parser.add_argument("--start-delay", type=int, choices=range(0, 31), default=12, metavar="0..30")
    args = parser.parse_args(argv)
    if args.window and len(args.window) > 2:
        parser.error("test obsługuje najwyżej dwie pozycje")
    if args.next_position and not args.editor_draft:
        parser.error("--next-position wymaga --editor-draft")
    if args.resume_pricing and (not args.editor_draft or args.next_position or len(args.window or ()) > 1):
        parser.error("--resume-pricing wymaga --editor-draft i przyjmuje co najwyżej jedno --window")
    if args.editor_draft and not args.window and not args.resume_pricing:
        parser.error("--editor-draft wymaga --window SZERxWYS")
    if args.next_position and len(args.window or ()) == 2:
        parser.error("Drugie --window już zleca wykonanie kolejnej pozycji")
    positions = tuple(args.window) if args.window else POSITIONS[:args.positions]
    leave_blank = frozenset(args.leave_blank or ())
    if leave_blank and (not args.window or args.resume_pricing or max(leave_blank) > len(positions)):
        parser.error("--leave-blank wymaga wymiarów danej pozycji podanych przez --window")
    if os.name != "nt" or not args.execute_live or any(
        os.environ.get(name) != "1" for name in ("COMPUTER_USE_LIVE", "WH_REAL_WINDOWHUB")
    ):
        print("WH_AUTONOMOUS_STOP=windows_and_explicit_live_test_required")
        return 4
    try:
        import cv2
        import mss
        import pyautogui
        from app.agent.offers.windowhub_customer_visual_selection import _ocr_engine

        if _ocr_engine() is None:
            raise ImportError("RapidOCR")
    except (ImportError, OSError, RuntimeError, ValueError) as exc:
        print("WH_AUTONOMOUS_STOP=editor_dependency_" + type(exc).__name__)
        return 4
    if not args.editor_draft:
        try:
            customer = input("Nazwa istniejącego klienta testowego: ").strip()
        except (EOFError, KeyboardInterrupt):
            return 4
        if not customer or len(customer) > 100 or any(ord(char) < 32 for char in customer):
            print("WH_AUTONOMOUS_STOP=invalid_test_customer")
            return 4

    from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
    from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window

    print(f"Przejdź do WindowHub. Start za {args.start_delay} s.", flush=True)
    time.sleep(args.start_delay)
    if not args.editor_draft and not activate_windowhub_workflow_window()[0]:
        print("WH_AUTONOMOUS_STOP=windowhub_activation_failed")
        return 4
    progress = OfferProgress()
    total_indices = ((2,) if args.window else ()) if args.resume_pricing else tuple(range(1, len(positions) + 1))
    failure = "position_not_attempted_or_unverified"
    try:
        loop, api = create_windows_desktop_agent_control_loop(), _Win32Mdi()
        if args.resume_pricing:
            return resume_draft_pricing(
                loop, api, args.editor_draft, args.window[0] if args.window else None,
                construction=args.construction, discount=args.discount, progress=progress,
            )
        if args.editor_draft:
            return build_selected_draft(
                loop, api, args.editor_draft, positions[0], construction=args.construction,
                next_position=args.next_position, discount=args.discount,
                next_size=positions[1] if len(positions) == 2 else None, leave_blank=leave_blank, progress=progress,
            )
        return run_from_start(
            loop, customer, api,
            require_customer_confirmation=True,
            on_offer_ready=lambda loop, offer, api: run_offer(
                loop, offer, api, positions, construction=args.construction, discount=args.discount,
                leave_blank=leave_blank, progress=progress,
            ),
        )
    except WorkspaceBlocked as exc:
        failure = str(exc)
        print("WH_AUTONOMOUS_STOP=" + failure, flush=True)
        print("WH_RECOVERY_NEXT=" + recovery_advice(str(exc)), flush=True)
        return 4
    except (OSError, RuntimeError, ValueError, ImportError) as exc:
        failure = "runtime_" + type(exc).__name__
        print("WH_AUTONOMOUS_STOP=" + failure, flush=True)
        return 4
    finally:
        remaining = [index for index in total_indices if all(p.index != index for p in progress.positions)]
        if remaining:
            progress.record(PositionResult(remaining[0], PositionStatus.BLOCKED, missing=(failure,)))
            for index in remaining[1:]:
                progress.record(PositionResult(index, PositionStatus.PENDING, missing=("not_attempted",)))
        report = progress.report()
        # Customer and save evidence are outside this editor/pricing report.
        print("WH_OFFER_POSITION_REPORT=" + json.dumps(report["positions"], ensure_ascii=False), flush=True)
        print("WH_SALESPERSON_REVIEW=" + json.dumps(progress.salesperson_review_report(), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
