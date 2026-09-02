import unittest

from app.catalog.profiles import PROFILE_CATALOG


class ProfileCatalogTests(unittest.TestCase):
    def test_veka_82_contains_default_components(self) -> None:
        profile = PROFILE_CATALOG["VEKA_82"]

        self.assertEqual(profile.name, "VEKA Softline 82 MD")
        self.assertEqual(profile.default_frame, "VEKA82_MD")
        self.assertEqual(profile.default_glass, "PERFECT_48")
        self.assertEqual(profile.default_hardware, "WINKHAUS_PRO")


if __name__ == "__main__":
    unittest.main()
