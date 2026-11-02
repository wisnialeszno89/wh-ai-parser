"""Run one NaviMind V2 goal against the active Windows desktop window."""

from __future__ import annotations

import argparse
import json

from app.agent.runtime.windows_desktop_v2_agent_runtime_factory import (
    create_windows_desktop_v2_agent_runtime,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute one bounded NaviMind V2 computer-use task."
    )
    parser.add_argument("--goal", required=True, help="Natural-language desktop task.")
    parser.add_argument("--max-cycles", type=int, default=10)
    args = parser.parse_args()

    runtime = create_windows_desktop_v2_agent_runtime()
    result = runtime.run(
        args.goal,
        max_cycles=args.max_cycles,
    )
    print("=== WINDOWS DESKTOP V2 RESULT ===")
    print(json.dumps({
        "task_id": result.task_id,
        "session_id": result.session_id,
        "success": result.success,
        "completed": result.completed,
        "requires_manual_review": result.requires_manual_review,
        "stopped": result.stopped,
        "reason": result.reason,
        "cycles": [
            {
                "cycle": item.cycle,
                "decision": item.decision,
                "action_name": item.action_name,
                "target": item.target,
                "executed": item.executed,
                "verified": item.verified,
                "reason": item.reason,
            }
            for item in result.cycles
        ],
    }, ensure_ascii=False, indent=2))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
