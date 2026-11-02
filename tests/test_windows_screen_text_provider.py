from types import SimpleNamespace

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.windows_screen_text_provider import (
    WindowsScreenTextProvider,
)


def _observation(image=object()):
    return EnvironmentObservation(
        state=EnvironmentState(
            active_application="EXCEL.EXE",
            active_window_title="Workbook - Excel",
            screen_width=100,
            screen_height=100,
        ),
        metadata={
            "screenshot": SimpleNamespace(
                image=image,
                width=100,
                height=100,
            ),
        },
    )


def _ocr_data():
    return {
        "text": ["Save", "workbook", "weak", ""],
        "conf": ["96", "90", "20", "-1"],
        "page_num": [1, 1, 1, 1],
        "block_num": [1, 1, 1, 1],
        "par_num": [1, 1, 1, 1],
        "line_num": [1, 1, 2, 3],
        "word_num": [1, 2, 1, 1],
        "left": [10, 52, 12, 0],
        "top": [20, 20, 60, 0],
        "width": [35, 42, 20, 0],
        "height": [12, 12, 9, 0],
    }


def test_windows_screen_text_provider_groups_words_and_emits_ocr_evidence():
    provider = WindowsScreenTextProvider(
        ocr_runner=lambda _image: _ocr_data(),
        min_confidence=35,
    )

    elements = provider.perceive(_observation())

    assert len(elements) == 1
    element = elements[0]
    assert element.kind == "text"
    assert element.label == "Save workbook"
    assert (element.x, element.y, element.width, element.height) == (
        10,
        20,
        84,
        12,
    )
    assert element.interaction_capability is InteractionCapability.NOT_INTERACTIVE
    assert element.metadata["source"] == "windows_ocr"
    assert element.metadata["ocr_word_count"] == 2
    assert [item.kind.value for item in element.evidence] == [
        "label",
        "text",
        "bounds",
    ]


def test_windows_screen_text_provider_returns_empty_without_screenshot():
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="EXCEL.EXE",
            active_window_title="Workbook - Excel",
            screen_width=100,
            screen_height=100,
        ),
    )

    provider = WindowsScreenTextProvider(
        ocr_runner=lambda _image: (_ for _ in ()).throw(
            AssertionError("OCR must not run without an image")
        )
    )

    assert provider.perceive(observation) == ()


def test_windows_screen_text_provider_fails_soft_when_ocr_engine_is_unavailable():
    observation = _observation()
    provider = WindowsScreenTextProvider(
        ocr_runner=lambda _image: (_ for _ in ()).throw(
            RuntimeError("tesseract unavailable")
        )
    )

    assert provider.perceive(observation) == ()
    assert observation.metadata["perception_diagnostics"]["windows_ocr"] == {
        "status": "unavailable",
        "reason": "RuntimeError",
    }


def test_windows_screen_text_provider_bounds_number_of_detected_lines():
    data = _ocr_data()
    data["text"] = ["one", "two", "three"]
    data["conf"] = ["90", "90", "90"]
    data["page_num"] = [1, 1, 1]
    data["block_num"] = [1, 1, 1]
    data["par_num"] = [1, 1, 1]
    data["line_num"] = [1, 2, 3]
    data["word_num"] = [1, 1, 1]
    data["left"] = [1, 2, 3]
    data["top"] = [1, 2, 3]
    data["width"] = [10, 10, 10]
    data["height"] = [5, 5, 5]

    provider = WindowsScreenTextProvider(
        ocr_runner=lambda _image: data,
        max_lines=2,
    )

    elements = provider.perceive(_observation())
    assert [item.label for item in elements] == ["one", "two"]
