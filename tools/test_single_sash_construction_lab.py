"""Verify ActivPilot direction and Inwersja on a single sash in the simulator."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.actions.models.action import Action
from app.agent.offers.windowhub_hardware_direction import plan_hardware_inversion
from app.knowledge.openings.opening_repository import OpeningRepository
from app.simulator.semantic_runner import SemanticWindowSimulator
from app.simulator.window_scene import WindowScene
from app.simulator.window_simulator import SINGLE_SASH_HARDWARE, WindowSimulator
from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowSide, WindowTopology


def check_single_sash(row, *, auto_direction="LEFT"):
    if row.get("construction") != "F004 DK-Fenster":
        raise ValueError("Pilotaż obsługuje konstrukcję F004 DK-Fenster.")
    code = row.get("opening")
    if code not in {"DKL", "DKR"}:
        raise ValueError("Oczekiwano kierunku DKL albo DKR.")
    repository = OpeningRepository()
    repository.DATA_PATH = ROOT / repository.DATA_PATH
    opening = repository.get_by_code_or_alias(code)
    if opening is None or opening.opening_type != "TILT_TURN" or opening.direction not in {"LEFT", "RIGHT"}:
        raise ValueError(f"Brak jednoznacznej definicji otwierania {code}.")
    width, height = row.get("width_mm"), row.get("height_mm")
    if any(type(value) is not int or value <= 0 for value in (width, height)):
        raise ValueError("Wymiary muszą być dodatnimi liczbami całkowitymi.")

    model = WindowModel(properties={"width": width, "height": height, "cells": 1})
    frame = model.add_element("frame", WindowElementType.FRAME)
    sash = model.add_element("sash", WindowElementType.SASH, parent_id=frame.id)
    topology = WindowTopology()
    topology.add(frame, side=WindowSide.CENTER)
    topology.add(sash, side=WindowSide.CENTER)

    simulator = WindowSimulator(WindowScene.empty(width, height), single_sash_auto_direction=auto_direction)
    runner = SemanticWindowSimulator(simulator)

    def apply(actions):
        result = simulator.apply(actions)
        if result.rejected:
            raise ValueError(f"Symulator odrzucił akcję: {result.rejected}")

    apply(runner.build_actions(model, topology))
    apply([Action("select_tool", tool_name="hardware_tool"), Action("select_hardware", value=SINGLE_SASH_HARDWARE)])
    before = read_single_sash(simulator.scene.semantic_snapshot(), width, height)
    if before.get("opening") != opening.opening_type:
        raise ValueError("Odczyt nie potwierdził rodzaju otwierania po wyborze ActivPilot.")
    requested = plan_hardware_inversion(opening.direction, before.get("direction"), before.get("inversion_checked"))
    if requested is not None:
        apply([Action("set_hardware_inversion", value="on" if requested else "off")])
    actual = simulator.scene.semantic_snapshot()
    after = read_single_sash(actual, width, height)
    if (
        after.get("opening") != opening.opening_type
        or after.get("direction") != opening.direction
        or (requested is not None and after.get("inversion_checked") is not requested)
    ):
        raise ValueError("Odczyt skrzydła nie potwierdził wymaganego otwierania.")
    return {
        "position": row["position"], "opening": code, "automatic_direction": before["direction"],
        "inversion_action": "unchanged" if requested is None else ("on" if requested else "off"),
        "final_direction": after["direction"], "scene": actual,
    }


def read_single_sash(actual, width, height):
    if actual["opening"] != {"width": width, "height": height}:
        raise ValueError("Wymiary konstrukcji różnią się od zlecenia.")
    elements = actual["elements"]
    if [element["kind"] for element in elements] != ["FRAME", "SASH"]:
        raise ValueError("Oczekiwano jednej ramy i jednego skrzydła bez słupka.")
    observed_frame, observed_sash = elements
    if observed_sash["parent_id"] != observed_frame["id"] or observed_sash["side"] != "center":
        raise ValueError("Odczyt nie potwierdził położenia skrzydła w ramie.")
    return observed_sash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft-file", type=Path, required=True)
    parser.add_argument("--position", action="append", help="Position reference. Defaults to 10.0 and 20.0.")
    parser.add_argument("--simulated-auto-direction", choices=("LEFT", "RIGHT", "UNKNOWN"), default="LEFT")
    args = parser.parse_args()
    references = args.position or ["10.0", "20.0"]
    try:
        draft = json.loads(args.draft_file.read_text(encoding="utf-8-sig"))
        if not isinstance(draft, dict) or draft.get("status") != "technical_draft" or not isinstance(draft.get("positions"), list):
            raise ValueError("Oczekiwano szkicu technicznego OCR.")
        results = []
        for reference in references:
            matches = [row for row in draft["positions"] if isinstance(row, dict) and row.get("position") == reference]
            if len(matches) != 1:
                raise ValueError(f"Brak jednoznacznej pozycji {reference}.")
            auto_direction = None if args.simulated_auto_direction == "UNKNOWN" else args.simulated_auto_direction
            results.append(check_single_sash(matches[0], auto_direction=auto_direction))
    except (OSError, ValueError) as exc:
        print(f"SINGLE_SASH_LAB_RESULT=review\n{exc}", file=sys.stderr)
        return 2
    for result in results:
        print(f"POSITION={result['position']} OPENING={result['opening']} AUTO_DIRECTION={result['automatic_direction']} "
              f"INVERSION={result['inversion_action']} FINAL_DIRECTION={result['final_direction']}")
    print("SINGLE_SASH_LAB_RESULT=verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
