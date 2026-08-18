from __future__ import annotations

import ctypes
import json
import struct
import time
from dataclasses import dataclass, asdict
from pathlib import Path

from app.runtime.execution.context.execution_context import ExecutionContext


user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

TB_BUTTONCOUNT = 0x0418
TB_GETBUTTON = 0x0417
TB_GETITEMRECT = 0x041D
TB_GETBUTTONTEXTW = 0x044B
TB_GETBUTTONINFOW = 0x043F
TB_GETSTATE = 0x0412

TBSTATE_CHECKED = 0x01
TBSTATE_PRESSED = 0x02
TBSTATE_ENABLED = 0x04
TBSTYLE_BUTTON = 0x00
TBSTYLE_SEP = 0x01

PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000
MEM_RELEASE = 0x8000
PAGE_READWRITE = 0x04


@dataclass
class ToolbarButton:
    index: int
    command_id: int
    state: int
    style: int
    image_index: int
    screen_rect: tuple[int, int, int, int] | None
    text: str


class RemoteMemory:
    def __init__(self, process, size: int):
        self.process = process
        self.size = size
        self.address = kernel32.VirtualAllocEx(
            process,
            None,
            size,
            MEM_COMMIT,
            PAGE_READWRITE,
        )
        if not self.address:
            raise RuntimeError("VirtualAllocEx failed")

    def write(self, data: bytes) -> None:
        written = ctypes.c_size_t()
        ok = kernel32.WriteProcessMemory(
            self.process,
            self.address,
            data,
            len(data),
            ctypes.byref(written),
        )
        if not ok or written.value != len(data):
            raise RuntimeError("WriteProcessMemory failed")

    def read(self, size: int) -> bytes:
        data = ctypes.create_string_buffer(size)
        read = ctypes.c_size_t()
        ok = kernel32.ReadProcessMemory(
            self.process,
            self.address,
            data,
            size,
            ctypes.byref(read),
        )
        if not ok:
            raise RuntimeError("ReadProcessMemory failed")
        return data.raw[: read.value]

    def __del__(self):
        address = getattr(self, "address", 0)
        process = getattr(self, "process", 0)
        if address and process:
            try:
                kernel32.VirtualFreeEx(process, address, 0, MEM_RELEASE)
            except Exception:
                pass


def _window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(max(length + 1, 256))
    user32.GetWindowTextW(hwnd, buf, len(buf))
    return buf.value.strip()


def _find_toolbar(hwnd_parent: int, wanted: str = "Narzędzia") -> int | None:
    found: list[int] = []

    enum_proc = ctypes.WINFUNCTYPE(
        ctypes.c_bool,
        ctypes.c_void_p,
        ctypes.c_void_p,
    )

    @enum_proc
    def cb(hwnd: int, _lparam: int) -> bool:
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, len(cls))
        if "Afx:ToolBar" in cls.value:
            title = _window_text(hwnd)
            if title == wanted:
                found.append(int(hwnd))
                return False
        return True

    user32.EnumChildWindows(hwnd_parent, cb, 0)
    return found[0] if found else None


def _get_window_rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = ctypes.wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise RuntimeError("GetWindowRect failed")
    return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top


def _get_process_id(hwnd: int) -> int:
    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return int(pid.value)


def _parse_tbbttn(raw: bytes, pointer_size: int) -> tuple[int, int, int, int]:
    # TBBUTTON:
    # bitmap, idCommand, fsState, fsStyle, dwData, iString
    if pointer_size == 4:
        if len(raw) < 20:
            raise RuntimeError("short 32-bit TBBUTTON")
        i_bitmap, id_command, state, style, _dw_data, i_string = struct.unpack(
            "<iiBBHII", raw[:20]
        )
    else:
        if len(raw) < 24:
            raise RuntimeError("short 64-bit TBBUTTON")
        i_bitmap, id_command, state, style, _padding, _dw_data, i_string = struct.unpack(
            "<iiBBHQq", raw[:24]
        )
    return int(i_bitmap), int(id_command), int(state), int(style)


def _toolbar_buttons(toolbar: int) -> list[ToolbarButton]:
    pid = _get_process_id(toolbar)
    process = kernel32.OpenProcess(
        PROCESS_QUERY_INFORMATION | PROCESS_VM_OPERATION | PROCESS_VM_READ | PROCESS_VM_WRITE,
        False,
        pid,
    )
    if not process:
        raise RuntimeError(f"OpenProcess failed for pid={pid}")

    try:
        count = int(user32.SendMessageW(toolbar, TB_BUTTONCOUNT, 0, 0))
        print(f"[NATIVE TOOLBAR] toolbar={toolbar} pid={pid} buttons={count}")

        pointer_size = 4
        # WindowHub is currently a 32-bit process, but keep the probe explicit.
        is_wow64 = ctypes.c_bool()
        machine = None
        if hasattr(kernel32, "IsWow64Process2"):
            process_machine = ctypes.c_ushort()
            native_machine = ctypes.c_ushort()
            ok = kernel32.IsWow64Process2(
                process,
                ctypes.byref(process_machine),
                ctypes.byref(native_machine),
            )
            if ok:
                machine = (process_machine.value, native_machine.value)
                if process_machine.value == 0:
                    pointer_size = 8
        print(f"[NATIVE TOOLBAR] machine={machine} pointer_size={pointer_size}")

        tbb_size = 20 if pointer_size == 4 else 24
        buttons: list[ToolbarButton] = []
        parent_rect = _get_window_rect(toolbar)

        for index in range(count):
            remote = RemoteMemory(process, tbb_size)
            zero = bytes(tbb_size)
            remote.write(zero)
            result = int(user32.SendMessageW(toolbar, TB_GETBUTTON, index, remote.address))
            if not result:
                print(f"[NATIVE TOOLBAR] TB_GETBUTTON failed index={index}")
                continue
            raw = remote.read(tbb_size)
            image_index, command_id, state, style = _parse_tbbttn(raw, pointer_size)

            rect_mem = RemoteMemory(process, 16)
            rect_mem.write(bytes(16))
            ok = int(user32.SendMessageW(toolbar, TB_GETITEMRECT, index, rect_mem.address))
            rect = None
            if ok:
                left, top, right, bottom = struct.unpack("<iiii", rect_mem.read(16))
                rect = (
                    parent_rect[0] + left,
                    parent_rect[1] + top,
                    right - left,
                    bottom - top,
                )

            text = ""
            text_mem = RemoteMemory(process, 512)
            text_mem.write(bytes(512))
            # TB_GETBUTTONTEXTW does not require remote buffer on some controls;
            # use the safer TB_GETBUTTONINFOW path first with remote memory.
            info_size = 56 if pointer_size == 4 else 72
            info = bytearray(info_size)
            struct.pack_into("<I", info, 0, info_size)
            # TBBUTTONINFOW: cbSize, dwMask, idCommand, iImage, fsState, fsStyle,
            # cx, lParam, pszText, cchText.
            TBIF_TEXT = 0x0002
            TBIF_COMMAND = 0x0020
            struct.pack_into("<I", info, 4, TBIF_TEXT | TBIF_COMMAND)
            if pointer_size == 4:
                struct.pack_into("<I", info, 12, image_index & 0xFFFFFFFF)
                struct.pack_into("<I", info, 36, text_mem.address & 0xFFFFFFFF)
                struct.pack_into("<I", info, 40, 240)
            else:
                struct.pack_into("<Q", info, 40, text_mem.address)
                struct.pack_into("<I", info, 48, 240)
            info_mem = RemoteMemory(process, info_size)
            info_mem.write(bytes(info))
            text_len = int(user32.SendMessageW(toolbar, TB_GETBUTTONINFOW, command_id, info_mem.address))
            if text_len >= 0:
                raw_text = text_mem.read(480)
                text = raw_text.decode("utf-16le", errors="ignore").split("\x00", 1)[0]

            print(
                f"[BUTTON {index:02}] id={command_id} image={image_index} "
                f"state=0x{state:02X} style=0x{style:02X} "
                f"enabled={bool(state & TBSTATE_ENABLED)} "
                f"checked={bool(state & TBSTATE_CHECKED)} "
                f"pressed={bool(state & TBSTATE_PRESSED)} "
                f"rect={rect} text={text!r}"
            )
            buttons.append(
                ToolbarButton(
                    index=index,
                    command_id=command_id,
                    state=state,
                    style=style,
                    image_index=image_index,
                    screen_rect=rect,
                    text=text,
                )
            )

        output = Path("outputs/debug/native_toolbar_buttons.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps([asdict(b) for b in buttons], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[NATIVE TOOLBAR] Saved: {output}")
        return buttons
    finally:
        kernel32.CloseHandle(process)


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE TOOLBAR BUTTON PROBE")
    print("=" * 80)
    print("DO NOT CLICK.")

    context = ExecutionContext(mouse_enabled=False)
    from app.runtime.execution.vision.runtime_vision import RuntimeVision

    vision = RuntimeVision().capture()
    context.window = vision.window
    print(
        f"[WINDOW] origin=({vision.window.left},{vision.window.top}) "
        f"size={vision.window.width}x{vision.window.height}"
    )

    toolbar = _find_toolbar(vision.window.hwnd, "Narzędzia")
    if toolbar is None:
        raise RuntimeError("Native Narzędzia toolbar was not found")

    print(f"[NATIVE TOOLBAR] hwnd={toolbar} rect={_get_window_rect(toolbar)}")
    _toolbar_buttons(toolbar)


if __name__ == "__main__":
    main()
