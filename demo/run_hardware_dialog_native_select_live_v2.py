import time

from app.runtime.execution.hardware_native_dialog_selector_v2 import (
    HardwareNativeDialogSelectorV2,
)


def main() -> None:
    print("=" * 80)
    print("NATIVE HARDWARE DIALOG SELECT LIVE V2")
    print("=" * 80)
    print("Expected state: hardware dialog is already open.")
    print("Target: UR ACTIVPILOT -> OK")
    time.sleep(0.5)

    selector = HardwareNativeDialogSelectorV2()
    selector.select_and_confirm(timeout_s=5.0)

    print("[NATIVE HARDWARE V2] UR ACTIVPILOT + OK ✅")


if __name__ == "__main__":
    main()
