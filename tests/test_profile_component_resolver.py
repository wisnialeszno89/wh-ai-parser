import unittest

from app.wh.resolvers.profile_component_resolver import ProfileComponentResolver


class ProfileComponentResolverTests(unittest.TestCase):
    def test_veka_softline_82_resolves_default_hardware(self) -> None:
        result = ProfileComponentResolver().resolve(
            "VEKA Softline 82 MD"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.profile.code, "VEKA_82")
        self.assertEqual(result.profile.name, "VEKA Softline 82 MD")

        self.assertEqual(
            result.hardware.code,
            "WINKHAUS_PRO",
        )
        self.assertEqual(
            result.hardware.manufacturer,
            "Winkhaus",
        )
        self.assertEqual(
            result.hardware.system,
            "activPilot Concept",
        )
        self.assertEqual(
            result.hardware.variant,
            "GAM/GAMA Z",
        )


if __name__ == "__main__":
    unittest.main()
