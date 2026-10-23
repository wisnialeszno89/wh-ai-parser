import json

from types import SimpleNamespace

import numpy as np

from app.agent.reasoning.navimind_task_reasoner import (
    NaviMindTaskReasoner,
    NaviMindTaskReasonerConfig,
)
from app.agent.reasoning.knowledge_context import (
    KnowledgeContext,
    KnowledgeFact,
    KnowledgeSource,
)
from app.agent.reasoning.task_planning_context import TaskPlanningContext
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.perception_engine import PerceptionEngine
from app.agent.perception.windowhub_ocr_provider import WindowHubOCRProvider
from app.agent.perception.windowhub_ocr_table_parser import WindowHubOCRTableRow
from app.agent.perception.windowhub_ocr_table_pipeline import WindowHubOCRTableReconstruction


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_navimind_reasoner_translates_semantic_action():
    captured = {}

    def opener(request, timeout):
        captured["body"] = request.data
        captured["timeout"] = timeout
        body = json.loads(request.data.decode("utf-8"))
        return _Response(
            {
                "version": "1",
                "task_id": body["task_id"],
                "status": "continue",
                "rationale": "Advance the visible workflow.",
                "confidence": 0.94,
                "action": {
                    "name": "click_screen_element",
                    "description": "Open the next visible section.",
                    "target": "Następna sekcja",
                },
                "requires_manual_review": False,
            }
        )

    reasoner = NaviMindTaskReasoner(
        config=NaviMindTaskReasonerConfig(
            url="http://localhost:3000/api/agent/task",
            timeout_seconds=12,
        ),
        opener=opener,
    )

    proposal = reasoner.reason(
        TaskPlanningContext(
            request_message="Otwórz następną sekcję",
            intent="computer_use",
            session_id="session-1",
            user_id="user-1",
        )
    )

    assert proposal is not None
    assert proposal.status == "continue"
    assert proposal.actions[0].target == "Następna sekcja"
    assert captured["timeout"] == 12
    body = json.loads(captured["body"].decode("utf-8"))
    assert body["version"] == "1"
    assert body["goal"] == "Otwórz następną sekcję"
    assert body["world"]["visible_elements"] == []
    assert body["knowledge"]["version"] == "1"
    assert body["knowledge"]["local"] is None
    assert body["knowledge"]["external"] is None


def test_navimind_reasoner_sends_explicit_allowed_actions():
    captured = {}

    def opener(request, timeout):
        captured["body"] = request.data
        captured["timeout"] = timeout
        return _Response(
            {
                "version": "1",
                "task_id": "task-1",
                "status": "continue",
                "rationale": "Use the visible control.",
                "confidence": 0.9,
                "action": {
                    "name": "click_screen_element",
                    "description": "Click the visible control.",
                    "target": "Następna sekcja",
                },
                "requires_manual_review": False,
            }
        )

    reasoner = NaviMindTaskReasoner(
        config=NaviMindTaskReasonerConfig(
            url="http://localhost:3000/api/agent/task",
            timeout_seconds=12,
        ),
        opener=opener,
    )

    # Capture the generated task id so the response satisfies the
    # correlation check introduced by the bridge.
    def correlated_opener(request, timeout):
        body = json.loads(request.data.decode("utf-8"))
        captured["task"] = body
        response = _Response(
            {
                "version": "1",
                "task_id": body["task_id"],
                "status": "continue",
                "rationale": "Use the visible control.",
                "confidence": 0.9,
                "action": {
                    "name": "click_screen_element",
                    "description": "Click the visible control.",
                    "target": "Następna sekcja",
                },
                "requires_manual_review": False,
            }
        )
        captured["timeout"] = timeout
        return response

    reasoner.opener = correlated_opener

    proposal = reasoner.reason(
        TaskPlanningContext(
            request_message="Otwórz następną sekcję",
            intent="computer_use",
        )
    )

    assert proposal is not None
    assert (
        "click_screen_element"
        in captured["task"]["constraints"]["allowed_actions"]
    )
    assert (
        "write_text"
        in captured["task"]["constraints"]["allowed_actions"]
    )
    assert len(
        captured["task"]["constraints"]["allowed_actions"]
    ) > 0
    assert captured["task"]["constraints"]["research_enabled"] is False


def test_navimind_reasoner_rejects_action_outside_local_policy():
    def opener(request, timeout):
        body = json.loads(request.data.decode("utf-8"))
        return _Response(
            {
                "version": "1",
                "task_id": body["task_id"],
                "status": "continue",
                "rationale": "Unsafe operation.",
                "confidence": 0.9,
                "action": {
                    "name": "execute_shell_command",
                    "description": "Run a local command.",
                },
                "requires_manual_review": False,
            }
        )

    reasoner = NaviMindTaskReasoner(
        config=NaviMindTaskReasonerConfig(
            url="http://localhost:3000/api/agent/task",
            timeout_seconds=12,
        ),
        opener=opener,
    )

    proposal = reasoner.reason(
        TaskPlanningContext(
            request_message="Zrób coś",
            intent="computer_use",
        )
    )

    assert proposal is None
    assert reasoner.last_error == "navimind_action_not_allowed"


def test_navimind_reasoner_rejects_task_id_mismatch():
    def opener(request, timeout):
        return _Response(
            {
                "version": "1",
                "task_id": "different-task",
                "status": "done",
                "rationale": "Done.",
                "confidence": 1.0,
                "action": None,
                "requires_manual_review": False,
            }
        )

    reasoner = NaviMindTaskReasoner(
        config=NaviMindTaskReasonerConfig(
            url="http://localhost:3000/api/agent/task",
            timeout_seconds=12,
        ),
        opener=opener,
    )

    proposal = reasoner.reason(
        TaskPlanningContext(
            request_message="Zakończ",
            intent="computer_use",
        )
    )

    assert proposal is None
    assert reasoner.last_error == "navimind_task_id_mismatch"

    
def test_navimind_reasoner_sends_structured_external_knowledge():
    captured = {}

    def opener(request, timeout):
        body = json.loads(request.data.decode("utf-8"))
        captured["body"] = body
        return _Response(
            {
                "version": "1",
                "task_id": body["task_id"],
                "status": "done",
                "rationale": "Knowledge was sufficient.",
                "confidence": 0.91,
                "action": None,
                "requires_manual_review": False,
            }
        )

    reasoner = NaviMindTaskReasoner(
        config=NaviMindTaskReasonerConfig(
            url="http://localhost:3000/api/agent/task",
        ),
        opener=opener,
    )

    knowledge = KnowledgeContext(
        status="complete",
        query="Product X glazing",
        sources=(
            KnowledgeSource(
                source_id="source-1",
                title="Manufacturer documentation",
                url="https://example.com/spec",
            ),
        ),
        facts=(
            KnowledgeFact(
                fact_id="fact-1",
                claim="Product X supports triple glazing.",
                source_ids=("source-1",),
                confidence=0.95,
                relevance=0.9,
            ),
        ),
    )

    proposal = reasoner.reason(
        TaskPlanningContext(
            request_message="Sprawdź produkt X.",
            intent="computer_use",
            external_knowledge=knowledge,
        )
    )

    assert proposal is not None
    assert captured["body"]["knowledge"]["version"] == "1"
    assert captured["body"]["knowledge"]["external"]["status"] == "complete"
    assert (
        captured["body"]["knowledge"]["external"]["facts"][0]["claim"]
        == "Product X supports triple glazing."
    )


def test_navimind_reasoner_enables_research_from_environment(monkeypatch):
    captured = {}

    def opener(request, timeout):
        body = json.loads(request.data.decode("utf-8"))
        captured["body"] = body
        return _Response(
            {
                "version": "1",
                "task_id": body["task_id"],
                "status": "done",
                "rationale": "Done.",
                "confidence": 1.0,
                "action": None,
                "requires_manual_review": False,
            }
        )

    monkeypatch.setenv("NAVIMIND_AGENT_RESEARCH_ENABLED", "1")
    monkeypatch.setenv("NAVIMIND_RESEARCH_MAX_RESULTS", "7")
    monkeypatch.setenv("NAVIMIND_RESEARCH_DEPTH", "advanced")
    monkeypatch.setenv("NAVIMIND_RESEARCH_TOPIC", "news")

    reasoner = NaviMindTaskReasoner(
        config=NaviMindTaskReasonerConfig(
            url="http://localhost:3000/api/agent/task",
        ),
        opener=opener,
    )

    proposal = reasoner.reason(
        TaskPlanningContext(
            request_message="Sprawdz informacje.",
            intent="computer_use",
        )
    )

    assert proposal is not None
    constraints = captured["body"]["constraints"]
    assert constraints["research_enabled"] is True
    assert constraints["research_max_results"] == 7
    assert constraints["research_depth"] == "advanced"
    assert constraints["research_topic"] == "news"


def test_navimind_reasoner_captures_returned_external_knowledge():
    captured = {}

    def opener(request, timeout):
        body = json.loads(request.data.decode("utf-8"))
        captured["body"] = body
        return _Response(
            {
                "version": "1",
                "task_id": body["task_id"],
                "status": "continue",
                "rationale": "Use the research-backed information.",
                "confidence": 0.92,
                "action": {
                    "name": "click_screen_element",
                    "description": "Open the visible product section.",
                    "target": "Produkt",
                },
                "requires_manual_review": False,
                "knowledge": {
                    "version": "1",
                    "local": None,
                    "external": {
                        "version": "1",
                        "status": "complete",
                        "query": "produkt specyfikacja",
                        "sources": [
                            {
                                "source_id": "web-1",
                                "title": "Manufacturer documentation",
                                "url": "https://example.com/spec",
                                "source_type": "web_search_result",
                            }
                        ],
                        "facts": [
                            {
                                "fact_id": "synth-fact-1",
                                "claim": "Product X supports triple glazing.",
                                "source_ids": ["web-1"],
                                "confidence": 0.84,
                                "relevance": 0.91,
                                "kind": "retrieved_evidence",
                            }
                        ],
                        "conflicts": [],
                        "limitations": [
                            "Not independently verified."
                        ]
                    }
                }
            }
        )

    reasoner = NaviMindTaskReasoner(
        config=NaviMindTaskReasonerConfig(
            url="http://localhost:3000/api/agent/task",
        ),
        opener=opener,
    )

    proposal = reasoner.reason(
        TaskPlanningContext(
            request_message="Sprawdź produkt X.",
            intent="computer_use",
        )
    )

    assert proposal is not None
    external = proposal.metadata["external_knowledge"]
    assert isinstance(external, dict)
    assert external["status"] == "complete"
    assert external["facts"][0]["fact_id"] == "synth-fact-1"

def test_navimind_reasoner_sends_structured_windowhub_table_in_world_metadata():
    captured = {}

    def opener(request, timeout):
        body = json.loads(request.data.decode("utf-8"))
        captured["body"] = body
        return _Response(
            {
                "version": "1",
                "task_id": body["task_id"],
                "status": "done",
                "rationale": "The observed table data is sufficient.",
                "confidence": 0.98,
                "action": None,
            }
        )

    row = WindowHubOCRTableRow(
        row_index=1,
        lp=4,
        lp_source="ocr",
        quantity=2,
        article="Okno",
        total_value="1045.18",
        unit_value="522.59",
        dimensions="1320 x 1345",
        center_y=223.9,
        missing_fields=(),
    )
    reconstruction = WindowHubOCRTableReconstruction((row,), (), ())
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHub",
            active_window_title="Okna - OFR/4170-",
        ),
        metadata={
            "windowhub_ocr_table_reconstruction": reconstruction,
        },
    )
    # The pipeline attaches reconstruction to observation metadata. The
    # WorldState bridge must preserve it even if scene metadata is empty.
    scene = ScreenScene(observation=observation, elements=(), metadata={})

    reasoner = NaviMindTaskReasoner(
        config=NaviMindTaskReasonerConfig(
            url="http://localhost:3000/api/agent/task",
        ),
        opener=opener,
    )
    proposal = reasoner.reason(
        TaskPlanningContext(
            request_message="Odczytaj pozycje oferty",
            intent="computer_use",
            scene=scene,
        )
    )

    assert proposal is not None
    world = captured["body"]["world"]
    table = world["metadata"]["windowhub_ocr_table"]
    assert table["row_count"] == 1
    assert table["rows"][0]["lp"] == 4
    assert table["rows"][0]["total_value"] == "1045.18"
    assert "center_y" not in table["rows"][0]
    assert world["visible_elements"] == []
    json.dumps(captured["body"], ensure_ascii=False)

def test_navimind_reasoner_preserves_partial_windowhub_rows_without_geometry():
    captured = {}

    def opener(request, timeout):
        body = json.loads(request.data.decode("utf-8"))
        captured["body"] = body
        return _Response(
            {
                "version": "1",
                "task_id": body["task_id"],
                "status": "done",
                "rationale": "The observed table has an unresolved row.",
                "confidence": 0.9,
                "action": None,
            }
        )

    rows = (
        WindowHubOCRTableRow(
            row_index=1,
            lp=1,
            lp_source="ocr_cell",
            quantity=1,
            article="Okno",
            total_value="826.29",
            unit_value="826.29",
            dimensions="800 x 1220",
            center_y=200.0,
            missing_fields=(),
        ),
        WindowHubOCRTableRow(
            row_index=2,
            lp=None,
            lp_source="missing",
            quantity=None,
            article="Okno",
            total_value="2275.50",
            unit_value="2275.50",
            dimensions="800 x 1190",
            center_y=300.0,
            missing_fields=("lp", "quantity"),
        ),
    )
    reconstruction = WindowHubOCRTableReconstruction(
        rows=rows,
        field_refinements=(),
        lp_refinements=(),
    )
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHub",
            active_window_title="Okna - OFR/4232-4202",
            screen_width=1920,
            screen_height=1080,
        ),
        metadata={"windowhub_ocr_table_reconstruction": reconstruction},
    )
    # Exercise the real NaviMind request builder without making a network call.
    scene = ScreenScene(observation=observation, elements=(), metadata={})
    reasoner = NaviMindTaskReasoner(
        config=NaviMindTaskReasonerConfig(
            url="http://localhost:3000/api/agent/task",
        ),
        opener=opener,
    )

    proposal = reasoner.reason(
        TaskPlanningContext(
            request_message="Odczytaj pozycje oferty",
            intent="computer_use",
            scene=scene,
        )
    )

    assert proposal is not None
    body = captured["body"]
    table = body["world"]["metadata"]["windowhub_ocr_table"]
    assert table["status"] == "partial"
    assert table["row_count"] == 2
    assert table["complete_row_count"] == 1
    assert table["rows"][0]["lp"] == 1
    assert table["rows"][0]["complete"] is True
    assert table["rows"][1]["lp"] is None
    assert table["rows"][1]["quantity"] is None
    assert table["rows"][1]["missing_fields"] == ["lp", "quantity"]
    assert table["rows"][1]["complete"] is False
    assert table["rows"][1]["total_value"] == "2275.50"
    assert body["world"]["visible_elements"] == []

    encoded = json.dumps(body, ensure_ascii=False)
    for forbidden in (
        '"center_y"',
        '"screen_width"',
        '"screen_height"',
        '"screenshot"',
        '"window_handle"',
        '"foreground_window_handle"',
    ):
        assert forbidden not in encoded

def test_navimind_reasoner_sends_table_from_live_perception_scene(monkeypatch):
    captured = {}

    class FakeOCREngine:
        def __init__(self):
            self.calls = 0

        def __call__(self, image):
            self.calls += 1
            return SimpleNamespace(
                txts=["Dokument"],
                boxes=[
                    np.array(
                        [[5, 5], [45, 5], [45, 20], [5, 20]],
                        dtype=float,
                    )
                ],
                scores=[0.99],
            )

    reconstruction = WindowHubOCRTableReconstruction(
        rows=(
            WindowHubOCRTableRow(
                row_index=1,
                lp=1,
                lp_source="ocr_cell",
                quantity=1,
                article="Okno",
                total_value="826.29",
                unit_value="826.29",
                dimensions="800 x 1220",
                center_y=200.0,
                missing_fields=(),
            ),
            WindowHubOCRTableRow(
                row_index=2,
                lp=None,
                lp_source="missing",
                quantity=None,
                article="Okno",
                total_value="2275.50",
                unit_value="2275.50",
                dimensions="800 x 1190",
                center_y=300.0,
                missing_fields=("lp", "quantity"),
            ),
        ),
        field_refinements=(),
        lp_refinements=(),
    )

    monkeypatch.setattr(
        "app.agent.perception.windowhub_ocr_provider.reconstruct_windowhub_ocr_table_rows",
        lambda elements, image, engine: reconstruction,
    )
    image = np.zeros((60, 100, 3), dtype=np.uint8)
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHub",
            active_window_title="Okna - OFR/4232-4202",
            screen_width=100,
            screen_height=60,
        ),
        metadata={
            "source": "windowhub",
            "window_focused": True,
            "screenshot": image,
        },
    )
    engine = FakeOCREngine()
    provider = WindowHubOCRProvider(engine=engine)
    scene = PerceptionEngine(providers=(provider,)).perceive(observation)

    def opener(request, timeout):
        body = json.loads(request.data.decode("utf-8"))
        captured["body"] = body
        return _Response(
            {
                "version": "1",
                "task_id": body["task_id"],
                "status": "done",
                "rationale": "The perceived table was serialized.",
                "confidence": 0.9,
                "action": None,
            }
        )

    reasoner = NaviMindTaskReasoner(
        config=NaviMindTaskReasonerConfig(
            url="http://localhost:3000/api/agent/task",
        ),
        opener=opener,
    )
    proposal = reasoner.reason(
        TaskPlanningContext(
            request_message="Odczytaj pozycje oferty",
            intent="computer_use",
            scene=scene,
        )
    )

    assert proposal is not None
    assert engine.calls == 1
    assert scene.metadata["windowhub_ocr_table_reconstruction"] is reconstruction
    assert scene.elements[0].interaction_capability is InteractionCapability.UNKNOWN

    body = captured["body"]
    world = body["world"]
    table = world["metadata"]["windowhub_ocr_table"]
    assert table["status"] == "partial"
    assert table["row_count"] == 2
    assert table["complete_row_count"] == 1
    assert table["rows"][0]["lp"] == 1
    assert table["rows"][1]["lp"] is None
    assert table["rows"][1]["quantity"] is None
    assert table["rows"][1]["missing_fields"] == ["lp", "quantity"]
    assert world["visible_elements"][0]["label"] == "Dokument"
    assert world["visible_elements"][0]["interaction_capability"] == "unknown"

    encoded = json.dumps(body, ensure_ascii=False)
    for forbidden in (
        '"center_y"',
        '"screen_width"',
        '"screen_height"',
        '"screenshot"',
        '"ocr_bounds"',
        '"window_handle"',
    ):
        assert forbidden not in encoded
    for element in world["visible_elements"]:
        assert not {"x", "y", "width", "height"}.intersection(element)




def test_navimind_reasoner_receives_active_windowhub_grid_as_structured_data():
    captured = {}

    def opener(request, timeout):
        body = json.loads(request.data.decode("utf-8"))
        captured["body"] = body
        return _Response(
            {
                "version": "1",
                "task_id": body["task_id"],
                "status": "done",
                "rationale": "Observed active-document grid data is sufficient.",
                "confidence": 0.97,
                "action": None,
            }
        )

    common = {
        "source": "windowhub_ui_automation",
        "uia_grid_cell_observation": True,
        "uia_grid_id": "private-runtime-grid-identity",
        "uia_grid_row_count": 1,
        "uia_grid_column_count": 2,
        "uia_grid_enumeration_truncated": False,
        "document_scope": "OFR/4170",
        "current_value_available": True,
        "current_value_source": "uia_legacy_accessible",
        "interaction_capability": "unknown",
    }
    width = ScreenElement(
        kind="gridcell",
        label="Szerokość",
        confidence=0.99,
        metadata={
            **common,
            "uia_grid_row_index": 0,
            "uia_grid_column_index": 0,
            "current_value": "1230",
            "uia_window_handle": 123456,
        },
    )
    blank = ScreenElement(
        kind="gridcell",
        label="Opis",
        confidence=0.99,
        metadata={
            **common,
            "uia_grid_row_index": 0,
            "uia_grid_column_index": 1,
            "current_value": "",
        },
    )
    scene = ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="WindowHub",
                active_window_title="Okna - OFR/4170",
            )
        ),
        elements=(width, blank),
        metadata={"active_document": "OFR/4170"},
    )

    context = TaskPlanningContext(
        request_message="Odczytaj siatkę aktywnej oferty",
        intent="computer_use",
        scene=scene,
    )
    scene_payload = context.to_payload()["scene"]
    structured_scene = scene_payload["structured_data"]["windowhub_grids"][0]
    assert structured_scene["rows"][0][0]["current_value"] == "1230"
    assert structured_scene["rows"][0][1]["current_value"] == ""
    assert structured_scene["rows"][0][1]["value_available"] is True
    assert all(
        item["kind"] != "gridcell"
        for item in scene_payload["visible_elements"]
    )
    assert "private-runtime-grid-identity" not in json.dumps(scene_payload)
    assert "uia_window_handle" not in json.dumps(scene_payload)

    reasoner = NaviMindTaskReasoner(
        config=NaviMindTaskReasonerConfig(
            url="http://localhost:3000/api/agent/task",
        ),
        opener=opener,
    )
    proposal = reasoner.reason(context)

    assert proposal is not None
    world_metadata = captured["body"]["world"]["metadata"]
    world_grid = world_metadata["windowhub_grids"][0]
    assert world_grid["document_scope"] == "OFR/4170"
    assert world_grid["rows"][0][0]["current_value"] == "1230"
    assert world_grid["rows"][0][1]["current_value"] == ""
    assert world_grid["rows"][0][1]["value_available"] is True
    assert all(
        item["kind"] != "gridcell"
        for item in captured["body"]["world"]["visible_elements"]
    )
    assert "private-runtime-grid-identity" not in json.dumps(world_metadata)
    assert "uia_window_handle" not in json.dumps(world_metadata)
    json.dumps(captured["body"], ensure_ascii=False)
