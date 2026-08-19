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
    the current native toolbar and current button RECT on every lookup, so
    moving the toolbar does not invalidate its coordinates.
    """

    ROOT_TITLE = "Okna -"
    TOOLBAR_TITLE = "Narzędzia"
    # Verified against the actual hardware icon and the successful live click:
    # toolbar index 17 / command 32792.
    DEFINITIONS = {
        GuiTool.HARDWARE: NativeToolDefinition(GuiTool.HARDWARE, 32792),
    }

    def __init__(self) -> None:
        self._root_hwnd: int | None = None

    def resolve(self, tool: GuiTool, window_left: int, window_top: int) -> ScreenElement:
        definition = self.DEFINITIONS.get(tool)
        if definition is None:
            raise RuntimeError(f"No native toolbar mapping for {tool.name}")

        root, toolbar = self._find_root_and_toolbar()
        self._root_hwnd = root
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
            f"root={root} toolbar={toolbar} toolbar_rect={toolbar_rect} "
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

    def _find_root_and_toolbar(self) -> tuple[int, int | None]:
        """Find WindowHub by its native toolbar, not only by caption text.

        The WindowHub caption can vary between runtime states. The MFC
        'Narzędzia' toolbar is a more stable native anchor, so inspect each
        visible top-level window and find the toolbar under it.
        """
        if self._root_hwnd and user32.IsWindow(self._root_hwnd):
            toolbar = _find_toolbar(self._root_hwnd, self.TOOLBAR_TITLE)
            if toolbar is not None:
                return self._root_hwnd, toolbar

        enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        found: list[tuple[int, int]] = []

        @enum
        def callback(hwnd: int, _lparam: int) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True
            toolbar = _find_toolbar(int(hwnd), self.TOOLBAR_TITLE)
            if toolbar is not None:
                found.append((int(hwnd), int(toolbar)))
                return False
            return True

        user32.EnumWindows(callback, 0)
        if found:
            root, toolbar = found[0]
            print(f"[NATIVE TOOLBAR] root_hwnd={root} toolbar={toolbar}")
            return root, toolbar

        # Diagnostic fallback: emit visible top-level windows instead of a
        # misleading title-only error.
        diagnostics: list[str] = []

        @enum
        def diagnostic_callback(hwnd: int, _lparam: int) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True
            title = ctypes.create_unicode_buffer(256)
            cls = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, title, len(title))
            user32.GetClassNameW(hwnd, cls, len(cls))
            title_value = title.value.strip()
            if title_value or "Afx" in cls.value:
                diagnostics.append(
                    f"hwnd={int(hwnd)} class={cls.value!r} title={title_value!r}"
                )
            return len(diagnostics) < 80

        user32.EnumWindows(diagnostic_callback, 0)
        for line in diagnostics:
            print(f"[WINDOW] {line}")

        raise RuntimeError(
            "WindowHub native toolbar was not found by top-level enumeration"
        )

    def _find_root_hwnd(self) -> int:
        root, _toolbar = self._find_root_and_toolbar()
        return root
