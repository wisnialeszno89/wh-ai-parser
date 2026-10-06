from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.learning.semantic_text_input_observer import SemanticTextInputTracker
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def _scene(fields):
    elements = tuple(
        ScreenElement(
            kind="edit",
            label=label,
            interaction_capability=InteractionCapability.CLICKABLE,
            metadata={
                "current_value": value,
                "uia_focused": focused,
            },
        )
        for label, value, focused in fields
    )

    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="WindowHub",
                active_window_title="New",
            )
        ),
        elements=elements,
    )


def test_tracker_coalesces_typing_into_one_semantic_write_event():
    tracker = SemanticTextInputTracker(settle_seconds=0.30)

    tracker.reset(_scene([("Szerokość", "", True)]))

    assert tracker.observe(
        _scene([("Szerokość", "1", True)]),
        now=0.10,
    ) == ()
    assert tracker.observe(
        _scene([("Szerokość", "12", True)]),
        now=0.20,
    ) == ()
    assert tracker.observe(
        _scene([("Szerokość", "1230", True)]),
        now=0.30,
    ) == ()

    events = tracker.observe(
        _scene([("Szerokość", "1230", True)]),
        now=0.61,
    )

    assert len(events) == 1
    assert events[0].action_type == "write_text"
    assert events[0].value == "1230"
    assert events[0].metadata["event_uia_name"] == "Szerokość"


def test_tracker_can_learn_clearing_a_field_as_empty_text():
    tracker = SemanticTextInputTracker(settle_seconds=0.20)

    tracker.reset(_scene([("Wysokość", "1450", True)]))

    assert tracker.observe(
        _scene([("Wysokość", "", True)]),
        now=0.10,
    ) == ()

    events = tracker.observe(
        _scene([("Wysokość", "", True)]),
        now=0.31,
    )

    assert len(events) == 1
    assert events[0].value == ""


def test_tracker_uses_focus_to_disambiguate_multiple_changed_fields():
    tracker = SemanticTextInputTracker(settle_seconds=0.10)

    tracker.reset(
        _scene([
            ("Szerokość", "", False),
            ("Wysokość", "", False),
        ])
    )

    scene = _scene([
        ("Szerokość", "1230", False),
        ("Wysokość", "1450", True),
    ])

    assert tracker.observe(scene, now=0.20) == ()

    events = tracker.observe(scene, now=0.31)

    assert len(events) == 1
    assert events[0].metadata["event_uia_name"] == "Wysokość"


def test_tracker_fails_closed_on_duplicate_semantic_field_keys():
    tracker = SemanticTextInputTracker(settle_seconds=0.0)

    tracker.reset(
        _scene([
            ("Szerokość", "", True),
            ("Szerokość", "", False),
        ])
    )

    events = tracker.observe(
        _scene([
            ("Szerokość", "1230", True),
            ("Szerokość", "1230", False),
        ]),
        now=0.1,
    )

    assert events == ()
