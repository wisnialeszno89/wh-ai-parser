from __future__ import annotations

import ctypes
from dataclasses import dataclass

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.models.screen_element import ScreenElement
from demo.run_native_toolbar_button_probe_live import _find_toolbar, _get_window_rect, _toolbar_buttons

user32 = ctypes.windll.user32


@dataclass(frozen=True)
class NativeToolDefinition:
    tool: GuiTool
    command_id: int


class NativeToolbarResolver:
    """Resolve known WindowHub tools from the native MFC toolbar.

    This deliberately does not use template matching. The resolver discovers
    the current toolbar HWND and current button RECT on every lookup, so moving
    the toolbar does not invalidate its coordinates.
    """

    ROOT_TITLE = "Okna -"
    TOOLBAR_TITLE = "Narzędzia"
    # Calibrated against the actual hardware icon found in the user's full
    # WindowHub screenshot: the crossed/diamond square at screen y≈772.
    # The corresponding native toolbar button is index 17 / command 32792.
    DEFINITIONS = {
        GuiTool.HARDWARE: NativeToolDefinition(GuiTool.HARDWARE, 32792),
    }

    def __init__(self) -> None:
        self._root_hwnd: int | None = None

    def resolve(self, tool: GuiTool, window_left: int, window_top: int) -> ScreenElement:
        definition = self.DEFINITIONS.get(tool)
        if definition is None:
            raise RuntimeError(f"No native toolbar mapping for {tool.name}")

        root = self._find_root_hwnd()
        toolbar = _find_toolbar(root, self.TOOLBAR_TITLE)
        if toolbar is None:
            raise RuntimeError("Native Narzędzia toolbar was not found")

        toolbar_rect = _get_window_rect(toolbar)
        buttons = _toolbar_buttons(toolbar)
        matches = [b for b in buttons if b.command_id == definition.command_id]
        if not matches:
            raise RuntimeError(
                f"Native toolbar command {definition.command_id} for {tool.name} was not found"
            )

        button = matches[0]
        if not (button.state & 0x04):
            print(
                f"[NATIVE TOOLBAR] {tool.name} command_id={button.command_id} "
                f"is disabled state=0x{button.state:02X} rect={button.screen_rect}"
            )
            raise RuntimeError(
                f"{tool.name} native toolbar button is inactive "
                f"(command_id={button.command_id}, state=0x{button.state:02X})"
            )

        if not button.screen_rect:
            raise RuntimeError(
                f"{tool.name} native toolbar button has no screen rectangle"
            )

        sx, sy, width, height = button.screen_rect
        local_x = sx - window_left
        local_y = sy - window_top

        print(
            f"[NATIVE TOOLBAR] {tool.name} command_id={button.command_id} "
            f"toolbar={toolbar} toolbar_rect={toolbar_rect} "
            f"screen_rect={button.screen_rect} local_rect=({local_x},{local_y},{width},{height})"
        )

        return ScreenElement(
            name=tool.name,
            x=int(local_x),
            y=int(local_y),
            width=int(width),
            height=int(height),
            confidence=1.0,
        )

    def _find_root_hwnd(self) -> int:
        if self._root_hwnd and user32.IsWindow(self._root_hwnd):
            return self._root_hwnd

        enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        found: list[int] = []

        @enum
        def callback(hwnd: int, _lparam: int) -> bool:
            title = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, title, len(title))
            if title.value.strip() == self.ROOT_TITLE:
                found.append(int(hwnd))
                return False
            return True

        user32.EnumWindows(callback, 0)
        if not found:
            raise RuntimeError(f"WindowHub root window not found: {self.ROOT_TITLE!r}")

        self._root_hwnd = found[0]
        print(f"[NATIVE TOOLBAR] root_hwnd={self._root_hwnd}")
        return self._root_hwnd
