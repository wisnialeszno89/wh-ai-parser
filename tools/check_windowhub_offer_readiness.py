"""Offline regression: access handoff, resumption, archived icons and two positions.

These observations are test fixtures, not observations of a running WindowHub.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.screen_element import ScreenElement

from app.agent.offers.windowhub_new_offer_mission import (
    NewWindowOfferGoal, NewWindowOfferMissionPlanner, OfferDecision,
)
from app.agent.offers.windowhub_position_mission import WindowPositionRequest


def scene(application="Okna.exe", title="", elements=()):
    return ScreenScene(EnvironmentObservation(EnvironmentState(
        active_application=application, active_window_title=title)), elements=elements)


def run_access_cases():
    goal = NewWindowOfferGoal(WindowPositionRequest(1, 1100, 1000))
    planner = NewWindowOfferMissionPlanner()
    password = ScreenElement(kind="edit", label="Passwort:", metadata={
        "source": "windowhub_ui_automation", "uia_visible": True})
    cases = [
        ("program_not_foreground", scene("powershell.exe"), OfferDecision.STOP_WRONG_ENVIRONMENT),
        ("login_required", scene(title="Logowanie"), OfferDecision.WAIT_USER_LOGIN),
        ("login_control", scene(title="WindowHub", elements=(password,)), OfferDecision.WAIT_USER_LOGIN),
        ("after_login_document", scene(title="Właściwości dokumentu"), OfferDecision.SELECT_TEST_CUSTOMER),
        ("after_login_position", scene(title="Dodawanie nowej pozycji"), OfferDecision.DELEGATE_POSITION),
    ]
    results = []
    for name, observation, expected in cases:
        decision = planner.decide(goal, observation)
        if decision.decision is not expected:
            raise ValueError(f"{name}: {decision.decision.value} != {expected.value}")
        results.append({"case": name, "decision": decision.decision.value,
                        "message": decision.reason, "evidence": "synthetic_scene"})
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--with-archive", action="store_true")
    parser.add_argument("--with-offer", action="store_true")
    args = parser.parse_args(argv)
    try:
        cases = run_access_cases()
        report = {"mode": "offline", "access_cases": cases, "live_actions": 0,
                  "status": "offline_checks_passed", "wh_offer_created": False}
        for case in cases:
            print(f"ACCESS_CASE={case['case']} DECISION={case['decision']}")
        if args.with_archive:
            from tools.check_windowhub_builder_sequence import main as check_archive
            if check_archive() != 0:
                raise ValueError("Nie potwierdzono ikon na archiwalnych zrzutach.")
            report["archived_icons"] = "matched_known_fixtures"
        if args.with_offer:
            from tools.check_windowhub_two_position_flow import run_headless, verify_saved
            request = json.loads((ROOT / "examples/windowhub-two-position-flow.json").read_text(encoding="utf-8"))
            offer = run_headless(request)
            verify_saved(offer, request)
            report["simulated_offer"] = offer
            print(f"OFFLINE_POSITIONS={len(offer['positions'])} SALES_REVIEW=required")
        if args.output:
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("WH_OFFER_READINESS_RESULT=offline_checks_passed LIVE_ACTIONS=0")
        return 0
    except (OSError, ValueError) as exc:
        print(f"WH_OFFER_READINESS_RESULT=review\n{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
