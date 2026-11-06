"""Evaluate an existing WindowHub teaching session without launching WindowHub."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_training_context import (
    read_demonstration_experience, read_demonstration_report,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Summarize a manual teaching recording")
    parser.add_argument("--demo", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = read_demonstration_report(args.demo)
        learned = read_demonstration_experience(args.demo)
    except (ValueError, OSError) as exc:
        print("DEMO_REPORT_ERROR=" + str(exc))
        return 2
    print("RECORDING=" + str(args.demo))
    print("OBSERVED_EVENTS=" + str(report["record_count"]))
    print("STAGE_PATH=" + " -> ".join(report["stage_sequence"]))
    print("FORM_STATE_CHANGE_EVENTS=" + str(report["within_stage_changes"]))
    print("UNRECOGNIZED_STAGE_EVENTS=" + str(report["unmapped_transitions"]))
    print("MODIFIER_OBSERVED=" + str(report["modifier_observed"]))
    print("EXPERIENCE_ITEMS_FOR_NAVIMIND=" + str(len(learned)))
    for item in learned:
        if "observed_from_stage" in item:
            print("LEARNED_TRANSITION=" + item["observed_from_stage"] + " -> " + item["observed_to_stage"])
        elif item.get("source") == "windowhub_construction_demonstration":
            print("LEARNED_CONSTRUCTION_STAGE=" + str(item.get("stage"))
                  + " group=" + str(item.get("construction_group"))
                  + " observed_field_changes="
                  + str(item.get("observed_field_state_changes")))
        elif item.get("control") is not None and item.get("observed_state") is not None:
            print("LEARNED_CONTROL_EFFECT=" + str(item["stage"]) + " "
                  + str(item["control"]) + " "
                  + str(item["observed_state"]) + "="
                  + str(item["observed_value"]))
        else:
            print("EXPERIENCE_UNCLASSIFIED=" + str(item.get("source", "unknown")))
    if not report["modifier_observed"]:
        print("NEXT_GAP=Modifier was not recognized; learn or identify the later WindowHub stages.")
    print("NOTE=Observations are evidence of transitions, not proof of specific clicked controls.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
