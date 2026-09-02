from app.catalog.hardware import HARDWARE_CATALOG, HardwareProduct


class HardwareResolver:

    def resolve(self, code: str) -> HardwareProduct | None:
        return HARDWARE_CATALOG.get(code)
