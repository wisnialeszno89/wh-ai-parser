"""Report WindowHub construction teaching progress from existing demo records.

Offline, read-only; no GUI actions, model calls or raw customer field values.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_construction_learning import (
    construction_map_coverage,
    construction_demonstration_report,
)
from app.agent.learning.windowhub_training_context import read_demonstration_records


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", type=Path, help="Existing redacted JSONL demonstration")
    args = parser.parse_args(argv)
    try:
        records = read_demonstration_records(args.demo) if args.demo else []
    except (OSError, ValueError) as exc:
        print("STOP =", type(exc).__name__)
        return 2
    known = construction_map_coverage()
    learned = construction_demonstration_report(records)
    print("=== WINDOWHUB CONSTRUCTION LEARNING ===")
    print("DEMO_RECORDS =", len(records))
    for group, mapping in known["mapped_groups"].items():
        progress = learned["construction_groups"][group]
        print("GROUP =", group,
              "STAGE =", mapping["stage"],
              "UIA_MAP =", mapping["status"],
              "STAGE_OBSERVED =", progress["stage_observed"],
              "FIELD_EFFECTS =", len(progress["fields_with_observed_effect"]),
              "FIELDS_TO_DEMONSTRATE =", ",".join(progress["fields_not_yet_demonstrated"]))
    print("STAGE_TRANSITIONS_OBSERVED =", len(learned["observed_stage_transitions"]))
    print("NOT_YET_MAPPED =", ",".join(known["pending_groups"]))
    print("FRAME_SASH_TOPOLOGY_LEARNED =", learned["frame_sash_topology_learned"])
    print("CATALOG_COMPATIBILITY_VERIFIED =", learned["catalog_compatibility_verified"])
    print("ACTIONS_EXECUTED = 0")
    print("MODEL_REQUESTS = 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
