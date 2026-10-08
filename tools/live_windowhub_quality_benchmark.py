from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.agent_request import AgentRequest
from app.agent.environment.windowhub_environment_adapter import (
    WindowHubEnvironmentAdapter,
)
from app.agent.perception.perception_engine import PerceptionEngine
from app.agent.perception.windowhub_form_reader import WindowHubFormReader
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)
from app.agent.perception.windowhub_vision_provider import (
    WindowHubVisionProvider,
)
from app.agent.runtime.windowhub_agent_runtime import (
    create_windowhub_agent_runtime,
)

from tools.inspect_live_windowhub_ui_targets import (
    _windowhub_hwnd,
    _window_title,
)
from tools.live_click_windowhub_target import _focus_window


FIELD_SYNONYMS = {
    "width": ("szerokość", "szer", "width"),
    "height": ("wysokość", "wys", "height"),
    "colour": ("kolor", "barwa", "ral"),
}


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _scenario_message() -> str:
    return (
        "Przygotuj nową ofertę w WindowHub. "
        f"Klient: {_env('AGENT_SMOKE_CUSTOMER', 'Test Client')}. "
        f"Produkt: {_env('AGENT_SMOKE_PRODUCT', 'okno')}. "
        f"Ilość: {_env('AGENT_SMOKE_QUANTITY', '1')}. "
        f"Wymiary: {_env('AGENT_SMOKE_WIDTH', '1230')} x "
        f"{_env('AGENT_SMOKE_HEIGHT', '1480')} mm. "
        f"Otwarcie: {_env('AGENT_SMOKE_OPENING', 'FIX')}. "
        f"Kolor: {_env('AGENT_SMOKE_COLOR', 'Biały')}."
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one real WindowHub autonomous task and report execution, "
            "reasoning-cost and semantic final-state quality evidence."
        )
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=12,
        help="Maximum observe/reason/act/verify cycles.",
    )
    parser.add_argument(
        "--max-reasoning-calls",
        type=int,
        default=8,
        help="Hard local reasoning-call budget.",
    )
    parser.add_argument(
        "--max-estimated-reasoning-cost-usd",
        type=float,
        default=None,
        help="Optional hard ceiling for estimated reasoning cost.",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=0.8,
        help="Seconds to wait after focusing WindowHub.",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Optional explicit session id.",
    )
    return parser.parse_args()


def _normalized(value: str | None) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().casefold().split())


def _numeric(value: str | None) -> str:
    if not isinstance(value, str):
        return ""
    return "".join(character for character in value if character.isdigit())


def _find_field(
    fields,
    role: str,
):
    synonyms = FIELD_SYNONYMS[role]

    for field in fields:
        label = _normalized(field.label)
        if not label:
            continue

        if any(
            synonym in label
            for synonym in synonyms
        ):
            return field

    return None


def _final_state_evidence(
    *,
    expected_width: str,
    expected_height: str,
    expected_colour: str,
):
    environment = WindowHubEnvironmentAdapter()
    observation = environment.observe()

    scene = PerceptionEngine(
        providers=(
            WindowHubVisionProvider(),
            WindowHubUIAutomationProvider(),
        ),
    ).perceive(observation)

    fields = WindowHubFormReader().read_active_document(scene)

    observed = {}
    checks = {}

    width = _find_field(fields, "width")
    height = _find_field(fields, "height")
    colour = _find_field(fields, "colour")

    observed["active_document"] = scene.active_document
    observed["fields"] = [
        {
            "label": field.label,
            "value": field.value,
            "document_scope": field.document_scope,
            "scope_status": field.scope_status,
        }
        for field in fields
    ]

    if width is None:
        checks["width"] = {
            "status": "inconclusive",
            "reason": "field_not_observed",
        }
    else:
        checks["width"] = {
            "status": (
                "verified"
                if _numeric(width.value)
                == _numeric(expected_width)
                else "mismatch"
            ),
            "label": width.label,
            "observed": width.value,
            "expected": expected_width,
        }

    if height is None:
        checks["height"] = {
            "status": "inconclusive",
            "reason": "field_not_observed",
        }
    else:
        checks["height"] = {
            "status": (
                "verified"
                if _numeric(height.value)
                == _numeric(expected_height)
                else "mismatch"
            ),
            "label": height.label,
            "observed": height.value,
            "expected": expected_height,
        }

    if colour is None:
        checks["colour"] = {
            "status": "inconclusive",
            "reason": "field_not_observed",
        }
    else:
        checks["colour"] = {
            "status": (
                "verified"
                if _normalized(colour.value)
                == _normalized(expected_colour)
                else "mismatch"
            ),
            "label": colour.label,
            "observed": colour.value,
            "expected": expected_colour,
        }

    statuses = {item["status"] for item in checks.values()}

    if "mismatch" in statuses:
        state = "mismatch"
    elif statuses == {"verified"}:
        state = "verified"
    else:
        state = "inconclusive"

    return {
        "state": state,
        "active_document": scene.active_document,
        "checks": checks,
        "observed": observed,
    }


def _print_summary(autonomous, final_state) -> None:
    execution = autonomous.execution_metrics
    quality = autonomous.quality_metrics
    cost = autonomous.reasoning_cost

    payload = {
        "success": autonomous.success,
        "completed": autonomous.completed,
        "requires_manual_review": autonomous.requires_manual_review,
        "stopped": autonomous.stopped,
        "reason": autonomous.reason,
        "reasoning_calls": autonomous.reasoning_calls,
        "reasoning_cost": cost.to_payload(),
        "execution_metrics": execution.to_payload(),
        "quality_metrics": quality.to_payload(),
        "final_state_evidence": final_state,
    }

    print()
    print("=" * 80)
    print("WINDOWHUB REAL E2E QUALITY BENCHMARK")
    print("=" * 80)
    print(f"success={autonomous.success}")
    print(f"completed={autonomous.completed}")
    print(f"manual_review={autonomous.requires_manual_review}")
    print(f"stopped={autonomous.stopped}")
    print(f"reason={autonomous.reason!r}")
    print(f"reasoning_calls={autonomous.reasoning_calls}")

    print()
    print("=== REASONING COST ===")
    print(f"provider={cost.provider!r}")
    print(f"model={cost.model!r}")
    print(f"input_tokens={cost.input_tokens}")
    print(f"cached_input_tokens={cost.cached_input_tokens}")
    print(f"output_tokens={cost.output_tokens}")
    print(f"total_tokens={cost.total_tokens}")
    print(f"reasoning_tokens={cost.reasoning_tokens}")
    print(f"estimated_cost_usd={cost.estimated_cost_usd}")

    print()
    print("=== EXECUTION METRICS ===")
    print(json.dumps(execution.to_payload(), ensure_ascii=False, sort_keys=True))

    print()
    print("=== QUALITY METRICS ===")
    print(json.dumps(quality.to_payload(), ensure_ascii=False, sort_keys=True))

    print()
    print("=== FINAL STATE EVIDENCE ===")
    print(json.dumps(final_state, ensure_ascii=False, indent=2, sort_keys=True))

    print()
    print("=== BENCHMARK VERDICT ===")
    print(
        "task_outcome="
        + ("PASS" if autonomous.success else "FAIL")
    )
    print(
        "semantic_final_state="
        + final_state["state"].upper()
    )
    print(
        "quality_state="
        + quality.quality_state
    )
    print()
    print("BENCHMARK_JSON=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


def main() -> int:
    load_dotenv()
    args = _parse_args()

    if os.environ.get("WH_REAL_WINDOWHUB") != "1":
        print(
            "ABORTED: Set WH_REAL_WINDOWHUB=1 for explicit LIVE "
            "WindowHub execution."
        )
        return 2

    if (
        os.environ.get("NAVIMIND_AGENT_URL", "").strip() == ""
        and os.environ.get("AGENT_TASK_REASONING") != "1"
    ):
        print(
            "ABORTED: Configure NAVIMIND_AGENT_URL or set "
            "AGENT_TASK_REASONING=1 to enable task reasoning."
        )
        return 2

    hwnd = _windowhub_hwnd()
    if hwnd is None:
        print("ABORTED: No visible WindowHub main window was found.")
        return 3

    if not _focus_window(hwnd):
        print(
            "ABORTED: WindowHub could not be made the foreground window."
        )
        return 4

    time.sleep(max(0.0, args.wait))

    session_id = args.session_id or f"quality-e2e-{uuid4().hex}"
    message = _scenario_message()

    print("Preparing REAL WindowHub E2E quality run")
    print("========================================")
    print(f"windowhub_hwnd={hwnd}")
    print(f"windowhub_title={_window_title(hwnd)!r}")
    print(f"session_id={session_id!r}")
    print(f"max_steps={args.max_steps}")
    print(f"max_reasoning_calls={args.max_reasoning_calls}")
    print(
        "max_estimated_reasoning_cost_usd="
        f"{args.max_estimated_reasoning_cost_usd}"
    )
    print(f"scenario={message}")

    runtime = create_windowhub_agent_runtime()

    autonomous = runtime.run_autonomous(
        AgentRequest(
            message=message,
            session_id=session_id,
        ),
        max_steps=max(1, args.max_steps),
        max_reasoning_calls=max(1, args.max_reasoning_calls),
        max_estimated_reasoning_cost_usd=(
            args.max_estimated_reasoning_cost_usd
        ),
    )

    final_state = _final_state_evidence(
        expected_width=_env("AGENT_SMOKE_WIDTH", "1230"),
        expected_height=_env("AGENT_SMOKE_HEIGHT", "1480"),
        expected_colour=_env("AGENT_SMOKE_COLOR", "Biały"),
    )

    _print_summary(autonomous, final_state)

    # A semantic field mismatch is a hard benchmark failure.
    # Missing fields remain inconclusive because the current WindowHub
    # scene may legitimately be on a non-form stage after completion.
    return_code = 0
    if not autonomous.success:
        return_code = 6
    elif final_state["state"] == "mismatch":
        return_code = 7

    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
