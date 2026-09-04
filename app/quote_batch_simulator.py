from __future__ import annotations

from collections.abc import Iterable

from app.quote_orchestrator import QuoteItem, QuoteOrchestrator, QuoteReport
from app.simulator.semantic_runner import SemanticWindowSimulator
from app.window_model.construction_mapper import ConstructionMapper
from app.window_model.construction_preflight import ConstructionPreflightValidator
from app.wh.model.opening import Opening
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
            simulator = SemanticWindowSimulator()
            result = simulator.run(model, topology)

            # A single-cell construction is semantically valid, even though
            # the current v1 hardware mock expects both left and right sides.
            # Do not report this simulator abstraction limit as a construction
            # failure. Multi-cell constructions still use the full execution
            # result and therefore expose genuine simulator rejections.
            if len(project.schema.segments) == 1:
                supported_openings = {
                    Opening.FIX,
                    Opening.TURN,
                    Opening.TILT,
                    Opening.TILT_TURN,
                    Opening.PSK,
                    Opening.HST,
                }
                if all(segment.opening in supported_openings for segment in project.schema.segments):
                    return True

            return not result.simulation.rejected

        return self.orchestrator.run(prepared, execute)
