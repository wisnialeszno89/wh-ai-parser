from app.wh.runtime.drivers.mouse_driver import (
    MouseDriver
)


class DriverResolver:

    @staticmethod
    def resolve_mouse():

        try:

            from app.wh.runtime.drivers.pyautogui_mouse_driver import (
                PyAutoGuiMouseDriver
            )

            print(
                "[DRIVER] "
                "PyAutoGUI loaded"
            )

            return (
                PyAutoGuiMouseDriver()
            )

        except Exception as e:

            print(
                f"[DRIVER] "
                f"fallback mock mouse: "
                f"{e}"
            )

            return MouseDriver()