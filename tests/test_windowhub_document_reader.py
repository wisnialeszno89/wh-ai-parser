from types import SimpleNamespace

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.windowhub_document_reader import (
    WindowHubDocumentReader,
)


class FakeInfo:
    def __init__(self, control_type, class_name="", name="", value=""):
        self.control_type = control_type
        self.class_name = class_name
        self.name = name
        self.value = value


class FakeItem:
    def __init__(self, info, *, value="", parent=None):
        self.element_info = info
        self._value = value
        self._parent = parent

    def parent(self):
        return self._parent

    def get_value(self):
        return self._value


class FakeWindow:
    def __init__(self, descendants):
        self._descendants = descendants

    def descendants(self):
        return tuple(self._descendants)


def make_scene(active_document="OFR/4024"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_window_title="Okna - WindowHub",
            ),
            metadata={"window_handle": 123},
        ),
        metadata={"active_document": active_document},
    )


def make_document(scope, value):
    window = FakeItem(
        FakeInfo("Window", name=scope),
    )
    document = FakeItem(
        FakeInfo("Document", class_name="RichTextBox"),
        value=value,
        parent=window,
    )
    return document


def test_reader_extracts_active_document_rich_text():
    scene = make_scene("OFR/4024")
    document = make_document(
        "OFR/4024",
        "•OSC1• SF_82 101.290 | 103.341 CIEMNOSZARY",
    )

    desktop = SimpleNamespace(
        window=lambda handle: SimpleNamespace(
            wrapper_object=lambda: FakeWindow([document])
        )
    )

    reader = WindowHubDocumentReader(
        desktop_factory=lambda: desktop,
    )

    documents = reader.read(scene)

    assert len(documents) == 1
    assert documents[0].document_scope == "OFR/4024"
    assert documents[0].control_type == "Document"
    assert documents[0].class_name == "RichTextBox"
    assert "SF_82" in documents[0].value


def test_reader_does_not_mix_other_document_content():
    scene = make_scene("OFR/4024")
    documents = [
        make_document("OFR/4024", "AKTYWNA OFERTA"),
        make_document("OFR/4025", "INNA OFERTA"),
    ]

    desktop = SimpleNamespace(
        window=lambda handle: SimpleNamespace(
            wrapper_object=lambda: FakeWindow(documents)
        )
    )

    reader = WindowHubDocumentReader(
        desktop_factory=lambda: desktop,
    )

    result = reader.read(scene)

    assert [item.value for item in result] == ["AKTYWNA OFERTA"]


def test_reader_returns_nothing_without_resolved_active_document():
    scene = make_scene(None)
    document = make_document("OFR/4024", "OFERTA")

    desktop = SimpleNamespace(
        window=lambda handle: SimpleNamespace(
            wrapper_object=lambda: FakeWindow([document])
        )
    )

    reader = WindowHubDocumentReader(
        desktop_factory=lambda: desktop,
    )

    assert reader.read(scene) == ()


def test_reader_ignores_non_document_controls():
    scene = make_scene("OFR/4024")
    window = FakeItem(FakeInfo("Window", name="OFR/4024"))
    text = FakeItem(
        FakeInfo("Text", class_name="TextBlock", name="SF_82"),
        value="SF_82",
        parent=window,
    )

    desktop = SimpleNamespace(
        window=lambda handle: SimpleNamespace(
            wrapper_object=lambda: FakeWindow([text])
        )
    )

    reader = WindowHubDocumentReader(
        desktop_factory=lambda: desktop,
    )

    assert reader.read(scene) == ()
