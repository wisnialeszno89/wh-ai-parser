import unittest

from app.catalog.profiles import PROFILE_CATALOG
from app.catalog.hardware import HARDWARE_CATALOG


class ProfileDefaultHardwareTests(unittest.TestCase):
    def test_veka_82_default_hardware_exists_in_catalog(self) -> None:
        profile = PROFILE_CATALOG["VEKA_82"]

        hardware = HARDWARE_CATALOG.get(
            profile.default_hardware
        )

        self.assertIsNotNone(hardware)
        self.assertEqual(hardware.code, "WINKHAUS_PRO")
        self.assertEqual(hardware.manufacturer, "Winkhaus")
        self.assertEqual(hardware.system, "activPilot Concept")
        self.assertEqual(hardware.variant, "GAM/GAMA Z")


if __name__ == "__main__":
    unittest.main()
