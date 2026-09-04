import unittest

from app.wh.runtime.construction_offer import ConstructionOffer
from app.wh.runtime.construction_parser import ConstructionParser
from app.wh.runtime.construction_normalizer import ConstructionNormalizer
from app.wh.runtime.features.profile_package import ProfilePackage
from app.window_model.construction_mapper import ConstructionMapper
from app.window_model.model import WindowElementType


class ConstructionMapperTests(unittest.TestCase):
    def test_two_sash_notation_maps_to_two_cell_window(self) -> None:
        schema = ConstructionParser().parse(
            ConstructionNormalizer().normalize("RU+RU")
        )
        schema.width = 2100
        schema.height = 1500

        model, topology = ConstructionMapper().map(schema)

        self.assertEqual(model.properties["width"], 2100)
        self.assertEqual(model.properties["height"], 1500)

        self.assertEqual(
            len(model.elements_of_type(WindowElementType.FRAME)),
            1,
        )
        self.assertEqual(
            len(model.elements_of_type(WindowElementType.SASH)),
            2,
        )
        self.assertEqual(
            len(model.elements_of_type(WindowElementType.GLASS)),
            2,
        )
        self.assertEqual(
            len(model.elements_of_type(WindowElementType.HARDWARE)),
            2,
        )

        self.assertIsNotNone(topology.node("sash_left"))
        self.assertIsNotNone(topology.node("sash_right"))

        self.assertEqual(
            model.elements["sash_left"].properties["opening"],
            "tilt_turn",
        )
        self.assertEqual(
            model.elements["sash_right"].properties["opening"],
            "tilt_turn",
        )

    def test_profile_system_never_becomes_hardware_system(self) -> None:
        schema = ConstructionParser().parse(
            ConstructionNormalizer().normalize("RU")
        )
        offer = ConstructionOffer(
            profile=ProfilePackage(
                manufacturer="VEKA",
                system="Softline 82 MD",
            )
        )

        model, _ = ConstructionMapper().map(schema, offer)

        hardware = model.elements["hardware_left"]
        self.assertEqual(hardware.properties["system"], "unknown")
        self.assertEqual(model.properties["profile_system"], "Softline 82 MD")


if __name__ == "__main__":
    unittest.main()
