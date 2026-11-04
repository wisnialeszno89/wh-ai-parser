"""NaviMind V2 goal runner: inspect / think / verified live actions."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.intake.task_document import read_task_document
from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.learning.windowhub_training_context import (read_demonstration_experience, read_demonstration_report, windowhub_skill_knowledge)
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.reasoning.navimind_task_reasoner_v2 import NaviMindTaskReasonerV2
from app.agent.runtime.computer_use_v2_action_session import ComputerUseV2ActionSession
from app.agent.runtime.windowhub_goal_v2_coordinator import execute_v2_step
from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Goal-driven WindowHub with NaviMind V2")
    parser.add_argument("--goal", help="Free-form Polish or German instruction")
    parser.add_argument("--task-file", type=Path, help="Client request (.txt/.md/.pdf)")
    parser.add_argument("--mode", choices=("inspect", "think", "execute"), default="inspect")
    parser.add_argument("--demo", type=Path)
    parser.add_argument("--max-actions", type=int, default=6)
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--approve-persistent", action="store_true")
    return parser.parse_args(argv)


def run_goal(loop, *, goal, reasoner, mode, max_actions, experience=(),
             approved_persistent=False):
    session = ComputerUseV2ActionSession()
    task_id = "wh-" + uuid4().hex[:16]
    feedback = list(experience)
    for revision in range(max_actions if mode == "execute" else 1):
        scene = enrich_windowhub_scene(loop.observe_scene())
        stage = stage_of(scene)
        if stage is None:
            print("STOP: WindowHub must be the foreground application.")
            return 4
        prepared = session.prepare_cycle(
            scene, task_id=task_id, session_id=task_id, goal=goal,
            world_revision=revision + 1, cycle=revision,
            max_cycles=max_actions, knowledge=windowhub_skill_knowledge(),
            experience=feedback[-12:],
            observed_at=datetime.now(timezone.utc).isoformat(),
        )
        actions = prepared.request_payload["capabilities"]["actions"]
        print(f"CYCLE={revision+1} STAGE={stage} ACTION_CAPABILITIES={len(actions)}")
        if mode == "inspect":
            entities = {e["ref"]: e for e in prepared.request_payload["world"]["entities"]}
            for item in actions[:24]:
                target = entities.get(item["target_ref"]) if item["target_ref"] else None
                print(f"CAPABILITY={item['name']} LABEL={(target or {}).get('label')}")
            print("INSPECT_ONLY: local capability inventory; no reasoning model was called and no UI action was performed.")
            return 0
        response = reasoner.reason(prepared.request_payload)
        if response is None:
            print("STOP: NAVIMIND_ERROR=" + str(reasoner.last_error))
            return 5
        print(f"REASONER_DECISION={response['decision']} CONFIDENCE={response['confidence']}")
        print(f"REASONER_REASON={str(response['rationale'])[:300]}")
        if response["decision"] == "done":
            print("DONE_VERIFIED=" + str(stage == "modifier"))
            return 0 if stage == "modifier" else 6
        if response["decision"] != "act" or response["confidence"] < .80:
            print("STOP: reasoner cannot yet choose a confident executable action.")
            return 4
        try:
            action = prepared.resolve_action_decision(response)
        except (ValueError, KeyError) as exc:
            print("STOP: invalid proposed action: " + str(exc))
            return 5
        print("PROPOSED_ACTION=" + action.action.name + " TARGET=" + str(getattr(action.action.target, "label", None)))
        if mode == "think":
            print("THINK_ONLY: nothing executed.")
            return 0
        try:
            execute_v2_step(loop, scene, action, approved_persistent=approved_persistent)
        except (ValueError, RuntimeError) as exc:
            print("STOP: local guard or verification: " + str(exc))
            return 6
        print("ACTION_VERIFIED=" + action.action.name)
        after = loop.observe_scene()
        feedback.append({
            "source": "local_verified_action",
            "from_stage": stage,
            "to_stage": stage_of(after) or "unknown",
            "action_type": action.action.name,
            "verified": True,
        })
    print("STOP: action budget exhausted; goal completion not assumed.")
    return 4


def main(argv=None):
    args = parse_args(argv)
    if os.name != "nt" or not 1 <= args.max_actions <= 20:
        return 2
    try:
        file_text = read_task_document(args.task_file) if args.task_file else ""
    except (ValueError, RuntimeError, OSError) as exc:
        print("STOP: document intake: " + str(exc))
        return 2
    goal = "\n".join(
        part for part in (args.goal or "", "Client request: " + file_text if file_text else "")
        if part.strip()
    )
    if not goal.strip() or len(goal) > 16000:
        print("STOP: --goal or --task-file required; empty or oversized request.")
        return 2
    if args.mode == "execute":
        if not args.execute_live or any(
            os.getenv(k) != "1" for k in ("WH_REAL_WINDOWHUB", "COMPUTER_USE_LIVE")
        ):
            print("STOP: --execute-live and both explicit desktop flags required.")
            return 2
        ok, info = activate_windowhub_workflow_window()
        print("WINDOWHUB_ACTIVATION=" + info)
        if not ok:
            return 3
    try:
        experience = read_demonstration_experience(args.demo) if args.demo else ()
        reasoner = NaviMindTaskReasonerV2() if args.mode != "inspect" else None
    except (RuntimeError, ValueError, OSError) as exc:
        print("STOP: NaviMind V2 configuration or demo error: " + str(exc))
        return 5
    if args.demo:
        report = read_demonstration_report(args.demo)
        print("DEMO_RECORDED_EVENTS=" + str(report["record_count"]))
        print("DEMO_STAGE_SEQUENCE=" + " -> ".join(report["stage_sequence"]))
        print("DEMO_FORM_STATE_EVENTS=" + str(report["within_stage_changes"]))
        print("DEMO_UNMAPPED_TRANSITIONS=" + str(report["unmapped_transitions"]))
        print("DEMO_EXPERIENCE_ITEMS=" + str(len(experience)))
        print("DEMO_MODIFIER_VERIFIED=" + str(report["modifier_observed"]))
    if args.mode != "inspect":
        print("NOTICE: goal and semantic scene are transmitted to configured NaviMind.")
    try:
        return run_goal(
            create_windows_desktop_agent_control_loop(),
            goal=goal, reasoner=reasoner, mode=args.mode,
            max_actions=args.max_actions, experience=experience,
            approved_persistent=args.approve_persistent,
        )
    except Exception as exc:
        print("STOP: " + type(exc).__name__ + ": " + str(exc)[:200])
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
