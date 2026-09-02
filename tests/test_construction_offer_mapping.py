import unittest

from app.wh.runtime.construction_offer import ConstructionOffer
from app.wh.runtime.construction_parser import ConstructionParser
from app.wh.runtime.construction_normalizer import ConstructionNormalizer
from app.wh.runtime.construction_schema import ConstructionSchema
from app.wh.runtime.features.accessory_package import AccessoryPackage
from app.wh.runtime.features.glass_package import GlassPackage
from app.wh.runtime.features.hardware_package import HardwarePackage
from app.wh.runtime.features.profile_package import ProfilePackage
from app.wh.runtime.features.security_package import SecurityPackage
from app.window_model.construction_mapper import ConstructionMapper
from app.window_model.model import WindowElementType


class ConstructionOfferMappingTests(unittest.TestCase):
    def test_offer_is_mapped_into_semantic_model(self) -> None:
        schema = ConstructionParser().parse(
            ConstructionNormalizer().normalize("RU+RU")
        )
        schema.width = 2100
        schema.height = 1500

        offer = ConstructionOffer(
            color_inside="WHITE",
            color_outside="ANTHRACITE",
            profile=ProfilePackage(
                manufacturer="VEKA",
                system="Softline 82",
            ),
            glass=GlassPackage(
                type="3glass",
                thickness_mm=44,
                warm_edge=True,
                swisspacer=True,
                security_p4=True,
            ),
            security=SecurityPackage(
                rc2=True,
                contacts=True,
            ),
            hardware=HardwarePackage(
                hidden_hinges=True,
                v_perfect=True,
            ),
            accessories=AccessoryPackage(
                roller_shutter="ROLETTE",
                sill="ALUMINIUM",
                mosquito_net=True,
                extension_mm=30,
                connector=True,
            ),
        )

        model, topology = ConstructionMapper().map(
            schema,
            offer,
        )

        self.assertEqual(model.properties["width"], 2100)
        self.assertEqual(model.properties["height"], 1500)

        self.assertEqual(model.properties["color_inside"], "WHITE")
        self.assertEqual(model.properties["color_outside"], "ANTHRACITE")

        self.assertEqual(model.properties["profile_manufacturer"], "VEKA")
        self.assertEqual(model.properties["profile_system"], "Softline 82")

        self.assertEqual(model.properties["glass_type"], "3glass")
        self.assertEqual(model.properties["glass_thickness_mm"], 44)
        self.assertTrue(model.properties["glass_warm_edge"])
        self.assertTrue(model.properties["glass_swisspacer"])
        self.assertTrue(model.properties["glass_security_p4"])

        self.assertTrue(model.properties["security_rc2"])
        self.assertTrue(model.properties["security_contacts"])

        self.assertTrue(model.properties["hardware_hidden_hinges"])
        self.assertTrue(model.properties["hardware_v_perfect"])

        self.assertEqual(model.properties["roller_shutter"], "ROLETTE")
        self.assertEqual(model.properties["sill"], "ALUMINIUM")
        self.assertTrue(model.properties["mosquito_net"])
        self.assertEqual(model.properties["extension_mm"], 30)
        self.assertTrue(model.properties["connector"])

        self.assertEqual(
            len(model.elements_of_type(WindowElementType.SASH)),
            2,
        )


if __name__ == "__main__":
    unittest.main()

    def test_profile_does_not_become_hardware_system(self) -> None:
        schema = ConstructionParser().parse(
            ConstructionNormalizer().normalize("RU+RU")
        )
        schema.width = 2100
        schema.height = 1500

        offer = ConstructionOffer(
            profile=ProfilePackage(
                manufacturer="VEKA",
                system="Softline 82 MD",
            )
        )

        model, _ = ConstructionMapper().map(schema, offer)

        self.assertEqual(
            model.elements["hardware_left"].properties["system"],
            "unknown",
        )
        self.assertEqual(
            model.elements["hardware_right"].properties["system"],
            "unknown",
        )


if __name__ == "__main__":
    unittest.main()

    def test_hardware_system_is_not_profile_system(self) -> None:
        schema = ConstructionParser().parse(
            ConstructionNormalizer().normalize("RU+RU")
        )
        schema.width = 2100
        schema.height = 1500

        offer = ConstructionOffer(
            profile=ProfilePackage(
                manufacturer="VEKA",
                system="Softline 82 MD",
            ),
            hardware=HardwarePackage(),
        )

        model, _ = ConstructionMapper().map(schema, offer)

        self.assertEqual(
            model.elements["hardware_left"].properties["system"],
            "unknown",
        )
        self.assertEqual(
            model.elements["hardware_right"].properties["system"],
            "unknown",
        )


if __name__ == "__main__":
    unittest.main()
