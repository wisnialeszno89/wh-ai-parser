import unittest

from app.quote_batch_simulator import QuoteBatchSimulator
from app.quote_orchestrator import QuoteItem
from app.wh.runtime.construction_normalizer import ConstructionNormalizer
from app.wh.runtime.construction_parser import ConstructionParser
from app.wh.runtime.construction_project import ConstructionProject
from app.wh.runtime.construction_offer import ConstructionOffer


class QuoteBatchSimulatorTests(unittest.TestCase):
    def _project(self, notation: str, width: int = 2100, height: int = 1500):
        schema = ConstructionParser().parse(
            ConstructionNormalizer().normalize(notation)
        )
        schema.width = width
        schema.height = height
        return ConstructionProject(schema=schema, offer=ConstructionOffer())

    def test_batch_executes_valid_items_and_skips_invalid_items(self) -> None:
        items = [
            QuoteItem("1", self._project("RU+RU")),
            QuoteItem("2", self._project("RU")),
            QuoteItem("3", self._project("RU", width=0)),
            QuoteItem("4", self._project("FIX+RU")),
            QuoteItem("5", self._project("RU+RU+RU")),
            QuoteItem("6", self._project("RU")),
        ]

        report = QuoteBatchSimulator().run(items)

        self.assertEqual(report.completed, ("1", "2", "4", "6"))
        self.assertEqual(report.skipped, ("3", "5"))
        self.assertEqual(report.failed, ())
        self.assertEqual(report.total, 6)

    def test_batch_does_not_stop_after_execution_failure(self) -> None:
        items = [
            QuoteItem("1", self._project("RU")),
            QuoteItem("2", self._project("RU")),
        ]

        simulator = QuoteBatchSimulator()
        original_mapper = simulator.mapper
        calls = 0

        class FailingMapper:
            def map_project(self, project):
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise RuntimeError("simulated mapping failure")
                return original_mapper.map_project(project)

        simulator.mapper = FailingMapper()
        report = simulator.run(items)

        self.assertEqual(report.completed, ("2",))
        self.assertEqual(report.failed, ("1",))
        self.assertEqual(report.skipped, ())


if __name__ == "__main__":
    unittest.main()
