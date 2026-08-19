import time

from app.runtime.execution.hardware_native_dialog_selector import (
    HardwareNativeDialogSelector,
)


def main() -> None:
    print("=" * 80)
    print("NATIVE HARDWARE DIALOG SELECT LIVE")
    print("=" * 80)
    print("Expected state: 'Wybór okuć: 1' dialog is already open.")
    print("Target: UR ACTIVPILOT -> OK")
    time.sleep(0.5)

    selector = HardwareNativeDialogSelector()
    selector.select_and_confirm(timeout_s=5.0)

    print("[NATIVE HARDWARE] UR ACTIVPILOT + OK ✅")


if __name__ == "__main__":
    main()
