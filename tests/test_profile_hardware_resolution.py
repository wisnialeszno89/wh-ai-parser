import unittest

from app.wh.resolvers.profile_resolver import ProfileResolver
from app.wh.resolvers.hardware_resolver import HardwareResolver


class ProfileHardwareResolutionTests(unittest.TestCase):
    def test_veka_82_has_default_winkhaus_hardware(self) -> None:
        profile = ProfileResolver().resolve("VEKA Softline 82 MD")

        self.assertEqual(profile, "VEKA_82")

        hardware = HardwareResolver().resolve("WINKHAUS_PRO")

        self.assertIsNotNone(hardware)
        self.assertEqual(hardware.manufacturer, "Winkhaus")
        self.assertEqual(hardware.system, "activPilot Concept")
        self.assertEqual(hardware.variant, "GAM/GAMA Z")


if __name__ == "__main__":
    unittest.main()
