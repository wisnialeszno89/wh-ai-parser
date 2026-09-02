import unittest

from app.wh.runtime.construction_parser import ConstructionParser
from app.wh.runtime.construction_normalizer import ConstructionNormalizer
from app.window_model.construction_mapper import ConstructionMapper
from app.simulator.semantic_runner import SemanticWindowSimulator
from app.window_model.model import WindowElementType


class ConstructionE2ETests(unittest.TestCase):
    def test_ru_ru_request_builds_complete_simulated_window(self) -> None:
        normalized = ConstructionNormalizer().normalize("RU+RU")
        schema = ConstructionParser().parse(normalized)

        schema.width = 2100
        schema.height = 1500

        model, topology = ConstructionMapper().map(schema)

        self.assertEqual(model.properties["width"], 2100)
        self.assertEqual(model.properties["height"], 1500)
        self.assertEqual(model.properties["cells"], 2)

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

        runner = SemanticWindowSimulator()
        result = runner.run(model, topology)

        self.assertEqual(result.simulation.rejected, ())
        self.assertTrue(
            runner.simulator.hardware_readiness().ready
        )
        self.assertEqual(
            runner.simulator.hardware.selected.product,
            "UR Activpilot",
        )


if __name__ == "__main__":
    unittest.main()
