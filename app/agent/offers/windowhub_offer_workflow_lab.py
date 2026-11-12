"""A local offer workflow that verifies each transition before committing a position."""

from copy import deepcopy

from app.agent.offers.windowhub_double_sash_lab import simulate_double_sash
from app.agent.offers.windowhub_single_sash_lab import simulate_single_tilt_turn
from tools.visual_offer_lab import matches_document


class OfferWorkflowLab:
    def __init__(self):
        self.stage = "start"
        self.document = None
        self.current = {}
        self.positions = []
        self.trace = []

    def _require(self, stage):
        if self.stage != stage:
            raise ValueError(f"Oczekiwano etapu {stage}, aktualny etap to {self.stage}.")

    def _advance(self, stage):
        self.trace.append({"from": self.stage, "to": stage, "saved_positions": len(self.positions)})
        self.stage = stage

    def new_offer(self):
        self._require("start")
        self._advance("document")

    def confirm_document(self, document):
        self._require("document")
        if not matches_document(document):
            raise ValueError("Wybierz dokładnie Top Trans i potwierdź preferencje testowe.")
        self.document = deepcopy(document)
        self._advance("item_type")

    def select_window(self, kind):
        self._require("item_type")
        if kind not in ("single", "double_fixed"):
            raise ValueError("Ten scenariusz obsługuje okno jedno- lub dwuskrzydłowe ze słupkiem stałym.")
        self.current = {"kind": kind}
        self._advance("dimensions")

    def set_dimensions(self, quantity, width_mm, height_mm):
        self._require("dimensions")
        if any(type(value) is not int or value <= 0 for value in (quantity, width_mm, height_mm)):
            raise ValueError("Ilość i wymiary w mm muszą być dodatnimi liczbami całkowitymi.")
        self.current.update(quantity=quantity, width_mm=width_mm, height_mm=height_mm)
        self._advance("color")

    def set_color(self, inside, outside):
        self._require("color")
        if inside not in ("biały", "antracyt") or outside not in ("biały", "antracyt"):
            raise ValueError("Wybierz kolor dla obu stron z listy testowej.")
        self.current.update(color_inside=inside, color_outside=outside)
        self._advance("builder")

    def build(self, specification):
        self._require("builder")
        row = {**specification, **self.current}
        if self.current["kind"] == "single":
            result = simulate_single_tilt_turn(row)
        else:
            result = simulate_double_sash(row)
        self.current.update(specification=deepcopy(specification), simulation=result)
        self._advance("position_review")

    def add_position(self):
        self._require("position_review")
        self.positions.append(deepcopy(self.current))
        self.current = {}
        self._advance("offer")

    def next_position(self):
        self._require("offer")
        self._advance("item_type")

    def save(self):
        self._require("offer")
        if not self.positions:
            raise ValueError("Oferta wymaga co najmniej jednej pozycji.")
        self._advance("saved")
        return {
            "status": "sales_review_required", "mode": "offline",
            "document": deepcopy(self.document), "positions": deepcopy(self.positions),
            "trace": deepcopy(self.trace),
        }
