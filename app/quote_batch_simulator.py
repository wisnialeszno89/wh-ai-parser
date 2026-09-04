from __future__ import annotations

from collections.abc import Iterable

from app.quote_orchestrator import QuoteItem, QuoteOrchestrator, QuoteReport
from app.simulator.semantic_runner import SemanticWindowSimulator
from app.window_model.construction_mapper import ConstructionMapper
from app.window_model.construction_preflight import ConstructionPreflightValidator
from app.wh.runtime.construction_project import ConstructionProject


class QuoteBatchSimulator:
    """Run a complete quote batch through preflight, mapping and the simulator."""

    def __init__(self) -> None:
        self.orchestrator = QuoteOrchestrator()
        self.validator = ConstructionPreflightValidator()
        self.mapper = ConstructionMapper()

    def run(self, items: Iterable[QuoteItem]) -> QuoteReport:
        prepared = self.orchestrator.preflight(items, self.validator)

        def execute(item: QuoteItem) -> bool:
            project = item.payload
            if not isinstance(project, ConstructionProject):
                return False
            model, topology = self.mapper.map_project(project)
            result = SemanticWindowSimulator().run(model, topology)
            # The deterministic simulator exposes rejected actions as its
            # execution failure signal. A fully applied plan is successful.
            return not result.simulation.rejected

        return self.orchestrator.run(prepared, execute)
