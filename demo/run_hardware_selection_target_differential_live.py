from __future__ import annotations

import time

import pyautogui

from app.runtime.execution.native_drawing_view_resolver import NativeDrawingViewResolver
from demo.run_native_toolbar_button_probe_live import _toolbar_buttons
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver


HARDWARE_COMMAND = 32792


def snapshot(label: str) -> dict[int, int]:
    resolver = NativeToolbarResolver()
    _root, toolbar = resolver._find_root_and_toolbar()
    if toolbar is None:
        raise RuntimeError("Native WindowHub toolbar not found")
    buttons = _toolbar_buttons(toolbar)
    state = {b.command_id: b.state for b in buttons if b.command_id}
    enabled = [cid for cid, value in state.items() if value & 0x04]
    print(f"[STATE {label}] enabled={enabled}")
    print(
        f"[STATE {label}] HARDWARE="
        f"0x{state.get(HARDWARE_COMMAND, 0):02X} "
        f"enabled={bool(state.get(HARDWARE_COMMAND, 0) & 0x04)}"
    )
    return state


def click_and_check(label: str, point: tuple[int, int]) -> None:
    print(f"[TARGET {label}] screen={point}")
    print("[CLICK] one controlled click in 2 seconds...")
    time.sleep(2.0)
    pyautogui.click(*point)
    time.sleep(0.8)
    snapshot(f"after_{label}")


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB HARDWARE SELECTION TARGET DIFFERENTIAL LIVE")
    print("=" * 80)
    print("CONTROLLED MODE: ONE CLICK PER RUN")

    view = NativeDrawingViewResolver().resolve()
    x, y, w, h = view["rect"]
    print(
        f"[DRAWING VIEW] hwnd={view['hwnd']} rect={view['rect']} "
        f"hits={view['hits']}"
    )

    # Re-use the known construction bbox from the safe native drawing-view
    # construction probe. We deliberately test the panel/interior separately
    # from the outer frame because HARDWARE may be enabled by sash selection,
    # not frame selection.
    bx, by, bw, bh = 80, 429, 373, 373
    points = {
        "sash_interior": (bx + bw // 2, by + bh // 2 + 20),
        "sash_top_inside": (bx + bw // 2, by + 28),
        "sash_left_inside": (bx + 28, by + bh // 2),
    }

    snapshot("before")
    name, point = next(iter(points.items()))
    click_and_check(name, point)
    print(
        "[ALTERNATIVES] "
        + ", ".join(f"{k}={v}" for k, v in list(points.items())[1:])
    )
    print("[PROBE] COMPLETE. Exactly one canvas click was sent.")


if __name__ == "__main__":
    main()
