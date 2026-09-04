import unittest

from app.quote_orchestrator import ItemStatus, QuoteItem, QuoteOrchestrator
from app.wh.runtime.construction_normalizer import ConstructionNormalizer
from app.wh.runtime.construction_parser import ConstructionParser
from app.wh.runtime.construction_project import ConstructionProject
from app.window_model.construction_preflight import ConstructionPreflightValidator


class ConstructionPreflightTests(unittest.TestCase):
    def _project(self, notation: str, width: int = 2100, height: int = 1500):
        schema = ConstructionParser().parse(
            ConstructionNormalizer().normalize(notation)
        )
        schema.width = width
        schema.height = height
        return ConstructionProject(schema=schema, offer=__import__(
            "app.wh.runtime.construction_offer",
            fromlist=["ConstructionOffer"],
        ).ConstructionOffer())

    def test_valid_project_is_ready(self) -> None:
        item = QuoteItem("1", self._project("RU+RU"))
        prepared = QuoteOrchestrator().preflight(
            [item], ConstructionPreflightValidator()
        )

        self.assertEqual(prepared[0].status, ItemStatus.READY)
        self.assertEqual(prepared[0].issues, [])

    def test_three_cells_are_blocked_before_mapping(self) -> None:
        item = QuoteItem("2", self._project("RU+RU+RU"))
        prepared = QuoteOrchestrator().preflight(
            [item], ConstructionPreflightValidator()
        )

        self.assertEqual(prepared[0].status, ItemStatus.SKIPPED)
        self.assertEqual(prepared[0].issues[0].code, "UNSUPPORTED_CELL_COUNT")

    def test_invalid_item_does_not_stop_valid_item(self) -> None:
        invalid = QuoteItem("bad", self._project("RU", width=0))
        valid = QuoteItem("good", self._project("RU"))

        orchestrator = QuoteOrchestrator()
        prepared = orchestrator.preflight(
            [invalid, valid], ConstructionPreflightValidator()
        )
        report = orchestrator.run(prepared, lambda _: True)

        self.assertEqual(report.skipped, ("bad",))
        self.assertEqual(report.completed, ("good",))
        self.assertEqual(report.failed, ())


if __name__ == "__main__":
    unittest.main()
