"""One synthetic, valid V2 reasoning request, no desktop or customer data.

Requires a successful prior tools/check_navimind_v2_connection.py check.
Only model response type/status is printed; no secrets or raw model content.
No GUI actions can occur: capabilities.actions is empty and no executor runs.
"""
from __future__ import annotations

import os
import sys

from app.agent.bridge.agent_task_contract_v2 import (
    validate_agent_task_v2_payload,
    validate_agent_task_v2_response,
)
from app.agent.reasoning.navimind_task_reasoner_v2 import NaviMindTaskReasonerV2


def synthetic_request() -> dict:
    """A minimal approved synthetic scene with one read-only observation."""
    return {
        "version": "2",
        "task_id": "synthetic-readonly-v2-smoke",
        "goal": (
            "Inspect the supplied synthetic table structure and decide "
            "whether a further read-only observation is useful. "
            "Do not propose desktop actions."
        ),
        "intent": "computer_use",
        "session_id": "synthetic-no-gui-session",
        "task_state": {
            "cycle": 0, "max_cycles": 2, "reasoning_calls_remaining": 1,
        },
        "world": {
            "revision": 1,
            "observed_at": "2026-11-26T10:00:00Z",
            "application": "SyntheticTableDemo",
            "window_title": "Synthetic test: no real app",
            "entities": [{
                "ref": "synthetic_table",
                "type": "table",
                "label": "Synthetic table",
                "state": {"visible": True, "enabled": True},
                "attributes": [],
                "confidence": 1.0,
                "evidence_refs": ["synthetic_evidence"],
            }],
            "relationships": [],
            "affordances": [],
            "evidence": [{
                "ref": "synthetic_evidence",
                "source": "synthetic_test",
                "observed_at": "2026-11-26T10:00:00Z",
                "world_revision": 1,
                "scope": "Synthetic table structure only",
                "confidence": 1.0,
                "content": {"kind": "table", "column_count": 2, "row_count": 3},
                "limitations": ["no_real_desktop", "no_customer_data"],
            }],
        },
        "capabilities": {
            "observations": [{
                "id": "inspect_synthetic_table",
                "description": "Read bounded synthetic table metadata",
                "target_ref": "synthetic_table",
                "input_contract": "table_page_v1",
                "max_items": 3,
                "data_classification": "synthetic",
                "read_only": True,
            }],
            "actions": [],
        },
        "knowledge": None,
        "experience": [],
        "constraints": {
            "max_observations_per_cycle": 1,
            "max_observation_items": 3,
            "max_evidence_bytes": 2048,
            "semantic_only": True,
            "verify_each_action": True,
        },
        "metadata": {},
    }


def run_once(reasoner=None) -> tuple[bool, str]:
    payload = synthetic_request()
    validate_agent_task_v2_payload(payload)
    if reasoner is None:
        reasoner = NaviMindTaskReasonerV2()
    answer = reasoner.reason(payload)
    if answer is None:
        # last_error only uses sanitized local transport/validation diagnostics.
        reason = str(reasoner.last_error or "no_valid_response")
        safe_reasons = {
            "navimind_http_400", "navimind_http_401", "navimind_http_403",
            "navimind_http_500", "navimind_http_502", "navimind_http_503",
            "navimind_http_504", "invalid_navimind_v2_json",
            "invalid_navimind_v2_response",
            "navimind_v2_response_too_large",
        }
        if reason not in safe_reasons:
            reason = reason.split(":", 1)[0][:80]
        return False, reason
    validate_agent_task_v2_response(answer, payload)
    return True, str(answer["decision"])


def main() -> int:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    if os.environ.get("COMPUTER_USE_LIVE") == "1":
        print("V2_SYNTHETIC_RESULT=blocked_live_environment")
        return 2
    try:
        ok, result = run_once()
    except Exception as exc:
        print("V2_SYNTHETIC_RESULT=failed")
        print("V2_SYNTHETIC_REASON=" + type(exc).__name__)
        return 1
    print("V2_SYNTHETIC_REAL_REASONING_REQUEST=True")
    print("V2_SYNTHETIC_CUSTOMER_DATA_TRANSMITTED=False")
    print("V2_SYNTHETIC_NATIVE_ACTIONS_AVAILABLE=False")
    print("V2_SYNTHETIC_RESULT=" + ("validated" if ok else "failed"))
    print("V2_SYNTHETIC_" + ("DECISION=" if ok else "REASON=") + result)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
