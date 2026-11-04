"""Let the salesperson demonstrate a complete WindowHub workflow.

Never clicks, types, records keystrokes, captures customer names, or sends data.
Samples observed UIA structure and emits only meaningful scene transitions.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import (
    semantic_snapshot, semantic_transition,
)
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Record semantic WindowHub teaching demo, no input actions.")
    p.add_argument("--seconds", type=int, default=180)
    p.add_argument("--interval", type=float, default=0.8)
    p.add_argument("--focus-delay", type=float, default=5)
    p.add_argument("--goal", default="Zademonstruj ofertę okna od początku do modyfikatora")
    p.add_argument("--output", type=Path, default=None)
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if os.name != "nt":
        print("Windows required.")
        return 2
    if not 5 <= args.seconds <= 1200 or not .3 <= args.interval <= 10 or not 0 <= args.focus_delay <= 30:
        print("Invalid recording limits.")
        return 2
    if not 1 <= len(args.goal) <= 300:
        print("Invalid goal.")
        return 2
    destination = args.output or (
        ROOT / "outputs" / "agent_learning"
        / ("windowhub-demo-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".jsonl")
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    loop = create_windows_desktop_agent_control_loop()
    print("DEMONSTRATION_MODE=READ_ONLY")
    print(f"LOG_FILE={destination}")
    print("The recorder does not click or capture customer data. Operate WindowHub manually.")
    print(f"Switch to WindowHub in {args.focus_delay:g} seconds.", flush=True)
    time.sleep(args.focus_delay)
    deadline = time.monotonic() + args.seconds
    previous = None
    count = 0
    errors = 0
    with destination.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "type": "session",
            "version": 1,
            "goal": args.goal,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "contains_raw_customer_values": False,
        }, ensure_ascii=False) + "\n")
        try:
            while time.monotonic() < deadline:
                try:
                    scene = enrich_windowhub_scene(loop.observe_scene())
                    snap = semantic_snapshot(scene)
                    if snap is not None:
                        if previous is None:
                            print("STAGE=" + str(snap["stage"]), flush=True)
                        else:
                            transition = semantic_transition(previous, snap)
                            if transition is not None:
                                record = {
                                    "type": "transition", "transition": transition,
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                }
                                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                                stream.flush()
                                count += 1
                                print(
                                    "OBSERVED " + str(transition["from_stage"])
                                    + " -> " + str(transition["to_stage"])
                                    + " changes=" + str(len(transition["changed"])),
                                    flush=True,
                                )
                        previous = snap
                    else:
                        # Do not connect observations across a switch to another app.
                        previous = None
                except Exception as exc:
                    errors += 1
                    if errors <= 3:
                        print("OBSERVATION_ERROR=" + type(exc).__name__, flush=True)
                    previous = None
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("Recording ended by operator.", flush=True)
    print(f"RECORDED_TRANSITIONS={count}")
    print(f"OBSERVATION_ERRORS={errors}")
    print(f"LOG_FILE={destination}")
    return 0 if count else 4


if __name__ == "__main__":
    raise SystemExit(main())
