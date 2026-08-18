"""Windows UI Automation controller for the WindowHub hardware dialog.

This module deliberately avoids screen coordinates. WindowHub exposes the hardware
selector as a standard Windows dialog, so the preferred strategy is to address the
actual dialog controls through UI Automation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HardwareUiTarget:
    name: str
    control_type: str
    text: str


class HardwareDialogUIA:
    DIALOG_TITLE_RE = r".*Wybór okuć.*"
    PREFERRED_ITEM = "UR ACTIVPILOT"
    OK_TEXT = "OK"

    def __init__(self) -> None:
        try:
            from pywinauto import Desktop
        except ImportError as exc:  # pragma: no cover - live Windows dependency
            raise RuntimeError(
                "pywinauto is required for semantic hardware dialog control. "
                "Install it with: python -m pip install pywinauto"
            ) from exc

        self._Desktop = Desktop
        self._dialog = None

    def attach(self):
        desktop = self._Desktop(backend="uia")
        try:
            dialog = desktop.window(title_re=self.DIALOG_TITLE_RE)
            dialog.wait("visible", timeout=5)
        except Exception as exc:
            raise RuntimeError("WindowHub hardware selection dialog was not found by UI Automation") from exc

        self._dialog = dialog
        print(f"[HARDWARE UIA] dialog found: {dialog.window_text()!r}")
        return dialog

    @property
    def dialog(self):
        if self._dialog is None:
            return self.attach()
        return self._dialog

    def _tree_items(self):
        items = self.dialog.descendants(control_type="TreeItem")
        result = []
        for item in items:
            try:
                text = item.window_text().strip()
            except Exception:
                continue
            if text:
                result.append((text, item))
        return result

    def find_tree_item(self, name: str | None = None):
        wanted = (name or self.PREFERRED_ITEM).strip()
        candidates = self._tree_items()

        # Prefer exact semantic text.  Only fall back to a startswith match when
        # there is no exact item, which helps with UIA exposing an extra suffix.
        for text, item in candidates:
            if text == wanted:
                print(f"[HARDWARE UIA] TreeItem exact: {text!r}")
                return item

        for text, item in candidates:
            if text.startswith(wanted):
                print(f"[HARDWARE UIA] TreeItem prefix: {text!r}")
                return item

        visible = [text for text, _ in candidates]
        print(f"[HARDWARE UIA] TreeItems visible: {visible[:30]}")
        return None

    def select_preferred_hardware(self, name: str | None = None) -> HardwareUiTarget:
        item = self.find_tree_item(name)
        if item is None:
            raise RuntimeError(
                f"Hardware TreeItem {name or self.PREFERRED_ITEM!r} was not found"
            )

        try:
            item.select()
        except Exception:
            item.click_input()

        item.wait("visible", timeout=2)
        text = item.window_text().strip()
        print(f"[HARDWARE UIA] selected: {text!r}")
        return HardwareUiTarget("hardware", "TreeItem", text)

    def find_ok_button(self):
        try:
            button = self.dialog.child_window(title=self.OK_TEXT, control_type="Button")
            button.wait("visible", timeout=3)
            return button
        except Exception as exc:
            buttons = []
            try:
                for button in self.dialog.descendants(control_type="Button"):
                    text = button.window_text().strip()
                    if text:
                        buttons.append(text)
            except Exception:
                pass
            print(f"[HARDWARE UIA] visible buttons: {buttons}")
            raise RuntimeError("Hardware dialog OK button was not found by UI Automation") from exc

    def confirm(self) -> HardwareUiTarget:
        button = self.find_ok_button()
        text = button.window_text().strip()
        button.click_input()
        print(f"[HARDWARE UIA] clicked: {text!r}")
        return HardwareUiTarget("confirm", "Button", text)

    def wait_closed(self, timeout: float = 5.0) -> bool:
        try:
            self.dialog.wait_not("visible", timeout=timeout)
            return True
        except Exception:
            try:
                return not self.dialog.exists(timeout=0.2)
            except Exception:
                return True
