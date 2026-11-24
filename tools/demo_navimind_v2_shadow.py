"""Run read-only synthetic V2/V3 shadow comparison in Linux Codespaces.

No Vercel calls, Windows access or credential requirements. No GUI actions.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.reasoning.navimind_v2_shadow_audit import (
    assess_v2_shadow, shadow_diagnostics,
)


def main() -> int:
    actions = [
        {
            "name": "click_ent_1", "target_ref": "virtual-add",
            "description": "Select item for an unsaved quotation",
            "requires_confirmation": False,
        },
        {
            "name": "save_offer", "target_ref": "virtual-save",
            "description": "Save quotation",
            "requires_confirmation": True,
        },
    ]
    response = {
        "decision": "act",
        "action": {"name": "click_ent_1", "target_ref": "virtual-add"},
    }
    report = assess_v2_shadow(
        stage="offer_document", actions=actions, response=response,
        exact_document_verified=True, observation_fresh=True,
    )
    print("SHADOW_SYNTHETIC_ONLY=True")
    print("WINDOWS_APPLICATION_CONNECTED=False")
    for key, value in shadow_diagnostics(report).items():
        print(str(key) + "=" + str(value))
    return 0 if report.proposal_decision == "act" and not report.execution_affected else 1


if __name__ == "__main__":
    raise SystemExit(main())
