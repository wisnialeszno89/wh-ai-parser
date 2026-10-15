from types import SimpleNamespace

import numpy as np

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.perception_engine import PerceptionEngine
from app.agent.perception.windowhub_ocr_provider import WindowHubOCRProvider


class FakeOCREngine:
    def __init__(self):
        self.calls = 0

    def __call__(self, image):
        self.calls += 1
        return SimpleNamespace(
            txts=["Dokument"],
            boxes=[np.array([[5, 5], [45, 5], [45, 20], [5, 20]], dtype=float)],
            scores=[0.99],
        )


def make_observation(*, title="Okna - OFR/4170- <>", source="windowhub", focused=True):
    image = np.zeros((60, 100, 3), dtype=np.uint8)
    return EnvironmentObservation(
        state=EnvironmentState(active_application="WindowHub", active_window_title=title, screen_width=100, screen_height=60),
        metadata={"source": source, "screenshot": image, "window_focused": focused},
    )


def test_reconstruction_is_attached_to_scene_metadata_without_changing_elements(monkeypatch):
    engine = FakeOCREngine()
    provider = WindowHubOCRProvider(engine=engine)
    reconstruction = SimpleNamespace(
        rows=(SimpleNamespace(complete=True), SimpleNamespace(complete=False)),
        field_refinements=(object(),),
        lp_refinements=(object(), object()),
    )
    captured = {}

    def fake_reconstruct(elements, image, supplied_engine):
        captured["elements"] = tuple(elements)
        captured["image_shape"] = image.shape
        captured["engine"] = supplied_engine
        return reconstruction

    monkeypatch.setattr("app.agent.perception.windowhub_ocr_provider.reconstruct_windowhub_ocr_table_rows", fake_reconstruct)
    observation = make_observation()
    scene = PerceptionEngine(providers=(provider,)).perceive(observation)
    assert scene.metadata["windowhub_ocr_table_status"] == "ok"
    assert scene.metadata["windowhub_ocr_table_reconstruction"] is reconstruction
    assert scene.metadata["windowhub_ocr_table_row_count"] == 2
    assert scene.metadata["windowhub_ocr_table_complete_row_count"] == 1
    assert scene.metadata["windowhub_ocr_table_field_refinement_count"] == 1
    assert scene.metadata["windowhub_ocr_table_lp_refinement_count"] == 2
    assert len(scene.elements) == 1
    assert scene.elements[0].label == "Dokument"
    assert scene.elements[0].interaction_capability == InteractionCapability.UNKNOWN
    assert captured["image_shape"] == (60, 100, 3)
    assert captured["engine"] is engine
    assert engine.calls == 1


def test_reconstruction_is_skipped_for_non_ofr_window(monkeypatch):
    provider = WindowHubOCRProvider(engine=FakeOCREngine())
    def fail(*args, **kwargs):
        raise AssertionError("table reconstruction should be skipped")
    monkeypatch.setattr("app.agent.perception.windowhub_ocr_provider.reconstruct_windowhub_ocr_table_rows", fail)
    observation = make_observation(title="WindowHub - Start")
    assert len(provider.perceive(observation)) == 1
    assert "windowhub_ocr_table_status" not in observation.metadata


def test_reconstruction_is_skipped_when_window_is_not_focused(monkeypatch):
    provider = WindowHubOCRProvider(engine=FakeOCREngine())
    def fail(*args, **kwargs):
        raise AssertionError("table reconstruction should be skipped")
    observation = make_observation(focused=False)
    monkeypatch.setattr("app.agent.perception.windowhub_ocr_provider.reconstruct_windowhub_ocr_table_rows", fail)
    assert len(provider.perceive(observation)) == 1
    assert "windowhub_ocr_table_status" not in observation.metadata


def test_table_reconstruction_failure_does_not_break_ocr_provider(monkeypatch):
    provider = WindowHubOCRProvider(engine=FakeOCREngine())
    def fail(*args, **kwargs):
        raise RuntimeError("test-only failure")
    observation = make_observation()
    monkeypatch.setattr("app.agent.perception.windowhub_ocr_provider.reconstruct_windowhub_ocr_table_rows", fail)
    elements = provider.perceive(observation)
    assert len(elements) == 1
    assert elements[0].label == "Dokument"
    assert observation.metadata["windowhub_ocr_table_status"] == "error"
    assert observation.metadata["windowhub_ocr_table_error"] == "RuntimeError"


def test_non_windowhub_observation_never_triggers_table_pipeline(monkeypatch):
    provider = WindowHubOCRProvider(engine=FakeOCREngine())
    def fail(*args, **kwargs):
        raise AssertionError("source guard should prevent table reconstruction")
    observation = make_observation(source="windows_desktop")
    monkeypatch.setattr("app.agent.perception.windowhub_ocr_provider.reconstruct_windowhub_ocr_table_rows", fail)
    assert len(provider.perceive(observation)) == 1
    assert "windowhub_ocr_table_status" not in observation.metadata
