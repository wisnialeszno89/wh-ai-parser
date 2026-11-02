"""Safe live smoke test for the WindowHub V2 Client Lookup/Grid path.

Run with the Client Lookup dropdown visible in the new-offer form.
Only structural UIA metadata is inspected; no UI text, values, headers,
cells, customer names, or business-record fields are requested.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Direct execution sets sys.path[0] to tools/, not the repository root.
_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from dataclasses import replace
import time

from app.agent.environment.windowhub_environment_adapter import (
    WindowHubEnvironmentAdapter,
)
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)
from app.agent.runtime.windowhub_lookup_grid_adapter import (
    WindowHubLookupGridAdapter,
)
from app.agent.runtime.windowhub_v2_observation_session import (
    WindowHubV2ObservationSession,
)


def main() -> int:
    prepared = None
    try:
        print(
            "SMOKE_PREPARE=Switch to WindowHub and open the Client dropdown "
            "during the next 10 seconds."
        )
        for remaining in range(10, 0, -1):
            print("SMOKE_STARTS_IN=" + str(remaining))
            time.sleep(1)

        raw_observation = WindowHubEnvironmentAdapter().observe()
        window_handle = raw_observation.metadata.get("window_handle")
        if (
            isinstance(window_handle, bool)
            or not isinstance(window_handle, int)
            or window_handle <= 0
        ):
            print("SMOKE_BLOCKED=WindowHub_window_handle_unavailable")
            return 2
        print(
            "WINDOWHUB_WINDOW_FOCUSED="
            + str(raw_observation.metadata.get("window_focused") is True)
        )
        foreground_handle = raw_observation.metadata.get(
            "foreground_window_handle"
        )
        root_owner_handle = raw_observation.metadata.get(
            "foreground_root_owner_handle"
        )
        app_root_owner_handle = raw_observation.metadata.get(
            "window_root_owner_handle"
        ) or window_handle
        print(
            "WINDOWHUB_ROOT_OWNER_AVAILABLE="
            + str(
                raw_observation.metadata.get("window_root_owner_handle")
                is not None
            )
        )
        print(
            "WINDOWHUB_OWNED_FOREGROUND_POPUP="
            + str(
                foreground_handle != window_handle
                and root_owner_handle == app_root_owner_handle
            )
        )

        # Do not forward the native window title into the V2 world.
        observation = replace(
            raw_observation,
            state=replace(
                raw_observation.state,
                active_window_title=None,
            ),
        )

        provider = WindowHubUIAutomationProvider()
        structural_diagnostics = []

        def collect_structural_diagnostic(record):
            if len(structural_diagnostics) < 80:
                structural_diagnostics.append(record)

        elements = provider.perceive_structure_only(
            observation,
            diagnostic_callback=collect_structural_diagnostic,
            diagnostic_limit=80,
        )
        scene = ScreenScene(
            observation=observation,
            elements=elements,
        )
        adapter = WindowHubLookupGridAdapter(provider=provider)
        session = WindowHubV2ObservationSession(
            lookup_grid_adapter=adapter,
        )
        prepared = session.prepare_cycle(
            scene,
            task_id="windowhub-v2-structure-smoke",
            goal="Inspect only the visible Client lookup grid structure.",
            intent="computer_use",
            world_revision=1,
        )

        print("STRUCTURE_ONLY_TABLE_CANDIDATES=" + str(len(elements)))
        print("UIA_STRUCTURAL_DIAGNOSTIC_COUNT=" + str(len(structural_diagnostics)))
        for index, record in enumerate(structural_diagnostics):
            print("UIA_NODE_" + str(index + 1) + "=" + repr(record))
        print(
            "CLIENT_LOOKUP_CAPABILITY_EXPOSED="
            + ("YES" if prepared.observation_capability is not None else "NO")
        )
        print("NAVI_MIND_HTTP_CALL=NO")

        if prepared.observation_capability is None:
            print("RESULT=CLIENT_LOOKUP_GRID_NOT_PROVEN")
            return 3

        descriptor = prepared.observation_capability
        response = {
            "version": "2",
            "task_id": prepared.task_id,
            "decision": "observe",
            "rationale": "Read bounded structural metadata for the visible lookup grid.",
            "confidence": 1.0,
            "observation_request": {
                "capability_id": descriptor["id"],
                "target_ref": descriptor["target_ref"],
                "parameters": {
                    "fields": [
                        "row_count",
                        "column_count",
                        "grid_pattern_available",
                        "table_pattern_available",
                    ]
                },
                "based_on_world_revision": prepared.world_revision,
            },
            "action": None,
            "completion": None,
            "requires_manual_review": False,
        }
        evidence = prepared.execute_observation_decision(response)
        fields = evidence["content"]["fields"]

        print("CLIENT_LOOKUP_GRID_LINKED=YES")
        print("GRID_ROW_COUNT=" + str(fields.get("row_count", "UNAVAILABLE")))
        print("GRID_COLUMN_COUNT=" + str(fields.get("column_count", "UNAVAILABLE")))
        print(
            "GRID_PATTERN_AVAILABLE="
            + str(fields.get("grid_pattern_available", "UNAVAILABLE"))
        )
        print(
            "TABLE_PATTERN_AVAILABLE="
            + str(fields.get("table_pattern_available", "UNAVAILABLE"))
        )
        print("CUSTOMER_TEXT_READ=NO")
        print("GRID_CELLS_READ=NO")
        print("RESULT=STRUCTURE_ONLY_SMOKE_PASSED")
        return 0
    except Exception as exc:
        print("SMOKE_FAILED=" + type(exc).__name__)
        return 1
    finally:
        if prepared is not None:
            prepared.revoke()


if __name__ == "__main__":
    raise SystemExit(main())
