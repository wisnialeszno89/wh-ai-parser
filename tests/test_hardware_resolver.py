import unittest

from app.wh.resolvers.hardware_resolver import HardwareResolver


class HardwareResolverTests(unittest.TestCase):
    def test_resolves_winkhaus_pro(self) -> None:
        hardware = HardwareResolver().resolve("WINKHAUS_PRO")

        self.assertIsNotNone(hardware)
        self.assertEqual(hardware.code, "WINKHAUS_PRO")
        self.assertEqual(hardware.manufacturer, "Winkhaus")
        self.assertEqual(hardware.system, "activPilot Concept")
        self.assertEqual(hardware.variant, "GAM/GAMA Z")

    def test_unknown_hardware_returns_none(self) -> None:
        self.assertIsNone(
            HardwareResolver().resolve("DOES_NOT_EXIST")
        )


if __name__ == "__main__":
    unittest.main()
