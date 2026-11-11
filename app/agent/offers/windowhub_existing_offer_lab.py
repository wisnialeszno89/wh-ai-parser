"""Edit one identified position in an existing offline offer with revision checks."""

from copy import deepcopy

from app.agent.offers.windowhub_double_sash_lab import simulate_double_sash, simulate_stulp
from app.agent.offers.windowhub_single_sash_lab import simulate_single_tilt_turn

_BUILDERS = {"single": simulate_single_tilt_turn, "double_fixed": simulate_double_sash, "stulp": simulate_stulp}


class ExistingOfferLab:
    def __init__(self, offers):
        self.offers = offers
        self.stage = "start"
        self.loaded = None
        self.original = None
        self.current = None
        self.reference = None
        self.trace = []

    def _require(self, expected):
        if self.stage != expected:
            raise ValueError(f"Oczekiwano etapu {expected}, aktualny etap to {self.stage}.")

    def _advance(self, stage):
        self.trace.append({"from": self.stage, "to": stage})
        self.stage = stage

    def existing_offer(self):
        self._require("start")
        self._advance("lookup")

    def load(self, number):
        self._require("lookup")
        matches = [offer for offer in self.offers if offer["number"] == number]
        if len(matches) != 1:
            raise ValueError("Nie znaleziono jednoznacznego numeru oferty.")
        self.original = deepcopy(matches[0])
        self.loaded = deepcopy(matches[0])
        self._advance("positions")

    def select_position(self, reference):
        self._require("positions")
        matches = [row for row in self.loaded["positions"] if row["reference"] == reference]
        if len(matches) != 1:
            raise ValueError("Nie znaleziono jednoznacznego numeru pozycji.")
        self.current = deepcopy(matches[0])
        self.reference = reference
        self._advance("edit")

    def correct(self, changes):
        self._require("edit")
        if not isinstance(changes, dict) or set(changes) - {"kind", "width_mm", "height_mm", "specification"}:
            raise ValueError("Nieobsługiwane pola korekty testowej.")
        candidate = {**self.current, **deepcopy(changes)}
        builder = _BUILDERS.get(candidate["kind"])
        if builder is None:
            raise ValueError("Brak symulatora dla wskazanej konstrukcji.")
        result = builder({**candidate["specification"], **candidate})
        candidate["simulation"] = result
        self.current = candidate
        self._advance("review")

    def save(self):
        self._require("review")
        matches = [offer for offer in self.offers if offer["number"] == self.loaded["number"]]
        if len(matches) != 1 or matches[0] != self.original:
            raise ValueError("Oferta zmieniła się od odczytu. Wczytaj ją ponownie przed zapisem.")
        positions = self.loaded["positions"]
        targets = [i for i, row in enumerate(positions) if row["reference"] == self.reference]
        if len(targets) != 1:
            raise ValueError("Numer pozycji nie jest jednoznaczny.")
        replacement = deepcopy(self.loaded)
        replacement["positions"][targets[0]] = deepcopy(self.current)
        replacement["revision"] += 1
        stored = matches[0]
        stored.clear()
        stored.update(deepcopy(replacement))
        self._advance("saved")
        return {"mode": "offline", "status": "sales_review_required", "changed_position": self.reference,
                "offer": deepcopy(stored), "trace": deepcopy(self.trace)}
