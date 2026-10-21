from types import SimpleNamespace

import numpy as np

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.windowhub_ocr_provider import WindowHubOCRProvider


class FakeEngine:
    def __init__(self, result=None, error=None):
        self.result = result or SimpleNamespace(
            txts=["OFR/4170", "Cena"],
            boxes=[
                np.asarray([[2, 2], [30, 2], [30, 15], [2, 15]], dtype=float),
                np.asarray([[35, 2], [55, 2], [55, 15], [35, 15]], dtype=float),
            ],
            scores=[0.99, 0.7],
        )
        self.error = error

    def __call__(self, image):
        if self.error:
            raise self.error
        return self.result


def observation(image=None):
    return EnvironmentObservation(
        state=EnvironmentState(active_window_title="WindowHub - Start"),
        metadata={"screenshot": np.zeros((60, 100, 3), dtype=np.uint8) if image is None else image},
    )


def test_provider_exposes_text_as_noninteractive_evidence():
    items = WindowHubOCRProvider(engine=FakeEngine()).perceive(observation())
    assert len(items) == 2
    assert items[0].label == "OFR/4170"
    assert items[0].interaction_capability is InteractionCapability.UNKNOWN
    assert items[0].metadata["interactive"] is False
    assert items[0].evidence[0].source.value == "ocr"


def test_provider_handles_missing_screenshot():
    target = observation()
    target.metadata.pop("screenshot")
    assert WindowHubOCRProvider(engine=FakeEngine()).perceive(target) == ()
    assert target.metadata["windowhub_ocr_status"] == "skipped_no_screenshot"


def test_provider_records_engine_errors_without_raising():
    target = observation()
    items = WindowHubOCRProvider(engine=FakeEngine(error=RuntimeError("fake"))).perceive(target)
    assert items == ()
    assert target.metadata["windowhub_ocr_status"] == "error"
    assert target.metadata["windowhub_ocr_error"] == "RuntimeError"


def test_provider_filters_low_confidence_and_invalid_boxes():
    result = SimpleNamespace(
        txts=["low", "invalid"],
        boxes=[
            np.asarray([[2, 2], [30, 2], [30, 15], [2, 15]], dtype=float),
            np.asarray([[200, 200], [210, 200], [210, 215], [200, 215]], dtype=float),
        ],
        scores=[0.1, 0.99],
    )
    items = WindowHubOCRProvider(engine=FakeEngine(result=result)).perceive(observation())
    assert items == ()
