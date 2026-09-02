import unittest

from app.wh.runtime.construction_offer import ConstructionOffer
from app.wh.runtime.construction_project import ConstructionProject
from app.wh.runtime.construction_parser import ConstructionParser
from app.wh.runtime.construction_normalizer import ConstructionNormalizer
from app.window_model.construction_mapper import ConstructionMapper


class ProjectMapperTests(unittest.TestCase):
    def test_construction_project_maps_to_window_model(self) -> None:
        schema = ConstructionParser().parse(
            ConstructionNormalizer().normalize("RU+RU")
        )
        schema.width = 2100
        schema.height = 1500

        offer = ConstructionOffer()
        offer.color_inside = "WHITE"
        offer.color_outside = "ANTHRACITE"
        offer.profile.manufacturer = "VEKA"
        offer.profile.system = "Softline 82"
        offer.glass.type = "3glass"
        offer.glass.thickness_mm = 44
        offer.hardware.hidden_hinges = True

        project = ConstructionProject(
            schema=schema,
            offer=offer,
        )

        model, topology = ConstructionMapper().map_project(project)

        self.assertEqual(model.properties["width"], 2100)
        self.assertEqual(model.properties["height"], 1500)
        self.assertEqual(model.properties["schema"], "RU+RU")
        self.assertEqual(model.properties["cells"], 2)

        self.assertEqual(
            model.properties["profile_manufacturer"],
            "VEKA",
        )
        self.assertEqual(
            model.properties["profile_system"],
            "Softline 82",
        )
        self.assertEqual(
            model.properties["glass_type"],
            "3glass",
        )
        self.assertEqual(
            model.properties["glass_thickness_mm"],
            44,
        )
        self.assertTrue(
            model.properties["hardware_hidden_hinges"],
        )

        self.assertEqual(
            len(topology.nodes),
            9,
        )


if __name__ == "__main__":
    unittest.main()
