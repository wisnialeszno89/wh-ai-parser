"""Opt-in remote NaviMind V2 compatibility probe using only a synthetic UI.

Sends exactly one V2 request to the configured, trusted endpoint. No desktop
observation, customers, screenshots, documents or real GUI actions are involved.
The server may call a billed model, so --allow-model-request is mandatory.
"""
from __future__ import annotations

# Allow both "python -m tools.<script>" and "python tools/<script>.py".
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
from datetime import datetime, timezone
from uuid import uuid4

from app.agent.reasoning.navimind_task_reasoner_v2 import (
    NaviMindTaskReasonerV2, NaviMindTaskReasonerV2Config,
)
from app.agent.runtime.computer_use_v2_action_session import ComputerUseV2ActionSession
from tools.run_windowhub_goal_v2 import shared_endpoint_v2_config
from tools.smoke_navimind_v2_offline import synthetic_scene


def make_probe_payload() -> dict[str, object]:
    scene = synthetic_scene("Okna - Start1")
    cycle = ComputerUseV2ActionSession().prepare_cycle(
        scene,
        task_id="v2-probe-" + uuid4().hex[:12],
        goal=(
            "Synthetic test: the screen has a button named NOWA OFERTA. "
            "Propose the best next action to begin a new offer; never execute it."
        ),
        world_revision=1,
        observed_at=datetime.now(timezone.utc).isoformat(),
        knowledge={"test_context": "Synthetic UI contract validation only. No real offer exists."},
    )
    return dict(cycle.request_payload)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="One-request NaviMind V2 server compatibility test")
    parser.add_argument("--allow-model-request", action="store_true")
    parser.add_argument("--reuse-shared-navimind-endpoint", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_model_request:
        print("STOP: This sends one request to the model-backed server and may incur a charge.")
        print("ACTION=Add --allow-model-request only after the NaviMind V2 deployment.")
        return 2

    try:
        config = (
            shared_endpoint_v2_config()
            if args.reuse_shared_navimind_endpoint
            else NaviMindTaskReasonerV2Config.from_environment()
        )
    except (ValueError, RuntimeError) as exc:
        print("STOP: server connection configuration is incomplete.")
        print("DETAIL_TYPE=" + type(exc).__name__)
        print("ACTION=Run python tools/diagnose_navimind_setup.py")
        return 3

    reasoner = NaviMindTaskReasonerV2(config=config)
    response = reasoner.reason(make_probe_payload())
    if response is None:
        print("V2_REMOTE_CONTRACT=FAILED")
        print("ERROR_CODE=" + str(reasoner.last_error))
        print("NOTE=This test did not interact with WindowHub.")
        return 4

    print("V2_REMOTE_CONTRACT=PASS")
    print("MODEL_DECISION=" + str(response.get("decision")))
    print("MODEL_CONFIDENCE=" + str(response.get("confidence")))
    action = response.get("action")
    print("MODEL_ACTION_KIND=" + str(action.get("name")) if isinstance(action, dict) else "MODEL_ACTION_KIND=None")
    print("NO_DESKTOP_ACTIONS_EXECUTED=True")
    print("NO_CUSTOMER_DATA_SENT=True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
