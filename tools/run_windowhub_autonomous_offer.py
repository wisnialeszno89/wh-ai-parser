"""Build a test offer using WindowHub's in-document drawing workspace."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import os
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.runtime.windowhub_mdi_native_probe import _Win32Mdi
from app.agent.runtime.windowhub_new_offer_handoff import (
    NewOfferHandoff, active_mdi_child, foreground_handle, owner_chain, scoped_position_stage,
)
from app.gui.enums.gui_tool import GuiTool
from tools.run_windowhub_existing_offer_position_test import (
    belongs_to_offer, inspect, run, run_from_start,
)
from tools.run_windowhub_two_position_live import (
    complete_discount, invoke_confirmation, open_next, owned_discount,
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
        from app.agent.learning.windowhub_builder_replay import read_builder_stage
        state = read_builder_stage(drawing.crop(rgb))
    else:
        state = fixed_window_stage(drawing.crop(rgb))
    return scene, rect, rgb, drawing, state


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
    name, scale = ARCHIVED_TEMPLATES[tool]
    with Image.open(ROOT / "templates" / name) as source:
        template = source.convert("L").resize(
            (round(source.width * scale), round(source.height * scale)), Image.Resampling.BILINEAR,
        )
    targets = []
    for toolbar in toolbars:
        x, y, width, height = _get_window_rect(toolbar)
        bounds = Box(x - rect.left, y - rect.top, width, height)
        if (
            bounds.x < 0 or bounds.y < 0 or bounds.right > rgb.shape[1]
            or bounds.bottom > rgb.shape[0] or height <= 2 * width or width <= 0
        ):
            continue
        gray = cv2.cvtColor(bounds.crop(rgb), cv2.COLOR_RGB2GRAY)
        hit = toolbar_tool(gray, np.asarray(template))
        if hit is not None:
            targets.append((toolbar, (bounds.x + hit[0], bounds.y + hit[1])))
    if len(targets) != 1:
        raise WorkspaceBlocked("construction_tool_unverified:" + tool.name)
    return targets[0]


def verify_editor_transition(scene, offer, api, number, size, *, opening):
    """Observe the wizard destination with the same vision that drives building."""
    from app.agent.learning.windowhub_builder_replay import NEXT_STEP, read_builder_stage
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
        classify = read_builder_stage if opening else fixed_window_stage
        state = classify(drawing.crop(image))
        if state not in {"empty", "frame", "sash"}:
            raise WorkspaceBlocked("unexpected_initial_drawing:" + state)
        step = (NEXT_STEP if opening else STEPS).get(state)
        if step is None:
            raise WorkspaceBlocked("unexpected_initial_drawing:" + state)
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
    if code in {"drawing_outline_unverified", "new_position_unverified"}:
        return "Odsłoń pole rysunku pod tabelą i sprawdź, czy widać cały obrys bieżącej pozycji."
    if code in {"selected_position_row_unverified", "selected_window_number_quantity_or_dimensions_unverified"}:
        return "Zaznacz w szkicu właściwy wiersz i sprawdź numer pozycji, ilość i wymiary z polecenia."
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
    initial_states = {"empty", "frame", "sash"} if fresh_draft and opening else {"empty"}
    if current[-1] not in initial_states:
        raise WorkspaceBlocked("new_position_unverified:" + current[-1])
    complete = "opening_marker" if opening else "fixed_glazed"
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


def run_offer(loop, offer, api, positions, *, construction="fix"):
    for number, size in enumerate(positions, 1):
        if number > 1:
            if isinstance(offer, NewOfferHandoff):
                if not offer.offer:
                    raise WorkspaceBlocked("next_position_requires_numbered_offer")
                offer = offer.offer
            predecessor = inspect(loop)
            scene = open_next(loop, predecessor, offer, api)
            if scene is not None and owned_discount(scene, offer, api):
                scene = complete_discount(loop, scene, offer, api, interactive=False)
            if scene is None or stage_of(scene) != "position" or not belongs_to_offer(scene, offer, api):
                raise WorkspaceBlocked("next_position_or_discount_unverified")
        print(f"WH_AUTONOMOUS_POSITION={number}:{size[0]}x{size[1]}", flush=True)
        status = run(
            loop, offer, api, stop_at_editor=True, width=size[0], height=size[1],
            allow_offer_workspace=True, editor_glazing_fallback=True,
            verify_editor=lambda scene, scope, api: verify_editor_transition(
                scene, scope, api, number, size, opening=construction == "ur",
            ),
        )
        if status:
            raise WorkspaceBlocked(f"position_wizard_unverified:{number}")
        if isinstance(offer, NewOfferHandoff):
            workspace = inspect(loop)
            if scoped_position_stage(workspace, offer, api) != "offer_document" or not belongs_to_offer(workspace, offer, api):
                raise WorkspaceBlocked("workspace_after_wizard_unverified:" + str(stage_of(workspace)))
        if construction == "ur":
            build_construction(loop, offer, api, number, size, opening=True)
        else:
            build_fixed(loop, offer, api, number, size)
    print(f"WH_AUTONOMOUS_RESULT=verified_draft_positions:{len(positions)}", flush=True)
    print("WH_AUTONOMOUS_PRICE_AND_SAVE=not_verified", flush=True)
    return 0


def observe_selected_draft_tab(scene, api, name):
    """Read only the visually selected tab and retain its image for rechecks."""
    import re
    import numpy as np
    import cv2
    from app.agent.learning.windowhub_offer_editor import selected_tab_crop_box
    from app.agent.offers.windowhub_customer_visual_selection import _ocr_text_results
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
    if names != [normalize(name)]:
        print("WH_DRAFT_EVIDENCE=" + ("different_active_draft" if len(names) == 1 else "active_tab_name_unverified"), flush=True)
        return None
    if foreground_handle(scene, api) != frame or active_mdi_child(frame, api) != child:
        print("WH_DRAFT_EVIDENCE=active_document_changed", flush=True)
        return None

    def check(rgb):
        return (
            foreground_handle(scene, api) == frame and active_mdi_child(frame, api) == child
            and selected_tab_crop_box(rgb) == box and np.array_equal(box.crop(rgb), crop)
        )

    print("WH_DRAFT_EVIDENCE=verified_visual_active_tab", flush=True)
    return check


def build_selected_draft(loop, api, name, size, *, construction):
    scene = inspect(loop)
    scope = NewOfferHandoff.bind_selected_draft(scene, api, name)
    if scope is None:
        check = observe_selected_draft_tab(scene, api, name)
        if check is not None:
            scope = NewOfferHandoff.bind_selected_draft(scene, api, name, visual_draft_check=check)
            if scope is None:
                print("WH_DRAFT_EVIDENCE=native_tab_conflicts_with_visual_name", flush=True)
    if scope is None:
        raise WorkspaceBlocked("requested_editor_draft_not_selected")
    opening = construction == "ur"
    if not verify_editor_transition(scene, scope, api, 1, size, opening=opening):
        raise WorkspaceBlocked("selected_editor_draft_not_verified")
    build_construction(loop, scope, api, 1, size, opening=opening)
    print("WH_AUTONOMOUS_RESULT=verified_draft_positions:1", flush=True)
    print("WH_AUTONOMOUS_PRICE_AND_SAVE=not_verified", flush=True)
    return 0


def window_size(value):
    import re
    match = re.fullmatch(r"\s*([0-9]{3,4})\s*[xX×]\s*([0-9]{3,4})\s*", value)
    if not match or not all(100 <= int(n) <= 5000 for n in match.groups()):
        raise argparse.ArgumentTypeError("podaj szerokość i wysokość w mm, np. 1200x1000")
    return tuple(map(int, match.groups()))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--construction", choices=("fix", "ur"), default="fix",
                        help="Rodzaj konstrukcji. UR to jedno skrzydło rozwierno-uchylne.")
    parser.add_argument("--editor-draft", metavar="DokumentN",
                        help="Buduj tylko pierwszą pozycję w zaznaczonym szkicu.")
    parser.add_argument("--positions", type=int, choices=(1, 2), default=2)
    parser.add_argument("--window", action="append", type=window_size, metavar="SZERxWYS",
                        help="Wymiary okna w mm. Powtórz opcję dla drugiej pozycji.")
    parser.add_argument("--start-delay", type=int, choices=range(0, 31), default=12, metavar="0..30")
    args = parser.parse_args(argv)
    if args.window and len(args.window) > 2:
        parser.error("test obsługuje najwyżej dwie pozycje")
    if args.editor_draft and len(args.window or ()) != 1:
        parser.error("--editor-draft wymaga dokładnie jednego --window SZERxWYS")
    positions = tuple(args.window) if args.window else POSITIONS[:args.positions]
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
    try:
        loop, api = create_windows_desktop_agent_control_loop(), _Win32Mdi()
        if args.editor_draft:
            return build_selected_draft(
                loop, api, args.editor_draft, positions[0], construction=args.construction,
            )
        return run_from_start(
            loop, customer, api,
            require_customer_confirmation=True,
            on_offer_ready=lambda loop, offer, api: run_offer(
                loop, offer, api, positions, construction=args.construction,
            ),
        )
    except WorkspaceBlocked as exc:
        print("WH_AUTONOMOUS_STOP=" + str(exc), flush=True)
        print("WH_RECOVERY_NEXT=" + recovery_advice(str(exc)), flush=True)
        return 4
    except (OSError, RuntimeError, ValueError, ImportError) as exc:
        print("WH_AUTONOMOUS_STOP=runtime_" + type(exc).__name__, flush=True)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
