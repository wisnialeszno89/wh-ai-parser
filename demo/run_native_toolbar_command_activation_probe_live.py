from __future__ import annotations

import ctypes
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from app.runtime.execution.vision.runtime_vision import RuntimeVision
from demo.run_native_toolbar_button_probe_live import _find_toolbar, _toolbar_buttons

user32 = ctypes.windll.user32

WM_COMMAND = 0x0111
TB_GETSTATE = 0x0412
TBSTATE_CHECKED = 0x01
TBSTATE_PRESSED = 0x02
TBSTATE_ENABLED = 0x04
KNOWN_HARDWARE_COMMAND_ID = 32789

@dataclass
class ActivationResult:
    index: int
    command_id: int
    before_states: dict[int, int]
    after_states: dict[int, int]
    changed_commands: list[int]
    activated_checked_commands: list[int]
    activated_pressed_commands: list[int]

def _find_root_hwnd() -> int:
    found: list[int] = []
    enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @enum
    def cb(hwnd: int, _lparam: int) -> bool:
        title = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, title, len(title))
        if title.value.strip() == "Okna -":
            found.append(int(hwnd))
            return False
        return True

    user32.EnumWindows(cb, 0)
    if not found:
        raise RuntimeError("WindowHub root window not found")
    return found[0]

def _button_state(toolbar: int, command_id: int) -> int:
    return int(user32.SendMessageW(toolbar, TB_GETSTATE, command_id, 0))

def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE TOOLBAR COMMAND ACTIVATION PROBE")
    print("=" * 80)
    print("SAFE MODE: WM_COMMAND only; canvas is never clicked.")
    print(f"[PROBE] skipping known HARDWARE command_id={KNOWN_HARDWARE_COMMAND_ID}")

    RuntimeVision().capture()
    root_hwnd = _find_root_hwnd()
    toolbar = _find_toolbar(root_hwnd, "Narzędzia")
    if toolbar is None:
        raise RuntimeError("Native Narzędzia toolbar was not found")

    buttons = _toolbar_buttons(toolbar)
    active = [
        b for b in buttons
        if b.command_id and (b.state & TBSTATE_ENABLED) and b.command_id != KNOWN_HARDWARE_COMMAND_ID
    ]
    command_ids = sorted({b.command_id for b in active})
    print(f"[PROBE] root={root_hwnd} toolbar={toolbar} active_commands={command_ids}")

    output_dir = Path("outputs/debug/native_toolbar_command_activation")
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[ActivationResult] = []

    for button in active:
        before_states = {cmd: _button_state(toolbar, cmd) for cmd in command_ids}
        print(f"[ACTIVATE] index={button.index} command_id={button.command_id} before=0x{before_states[button.command_id]:02X}")

        # ctypes has no wparam constructor. WM_COMMAND's wParam is an integer
        # command identifier; SendMessageW accepts it directly as a WPARAM value.
        user32.SendMessageW(root_hwnd, WM_COMMAND, int(button.command_id), 0)
        time.sleep(0.35)

        after_states = {cmd: _button_state(toolbar, cmd) for cmd in command_ids}
        changed = [cmd for cmd in command_ids if after_states[cmd] != before_states[cmd]]
        checked = [cmd for cmd in command_ids if after_states[cmd] & TBSTATE_CHECKED]
        pressed = [cmd for cmd in command_ids if after_states[cmd] & TBSTATE_PRESSED]
        print(f"[ACTIVATE] command_id={button.command_id} changed={changed} checked={checked} pressed={pressed}")

        results.append(ActivationResult(button.index, button.command_id, before_states, after_states, changed, checked, pressed))
        time.sleep(0.15)

    output = output_dir / "command_activation.json"
    output.write_text(json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[PROBE] Saved: {output}")
    print("[PROBE] COMPLETE. No canvas click was sent.")

if __name__ == "__main__":
    main()
