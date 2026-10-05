from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.perception_engine import (
    PerceptionEngine,
)
from app.agent.perception.screen_element import (
    ScreenElement,
)


def make_observation():
    return EnvironmentObservation(
        state=EnvironmentState(
            active_window_title="Okna - Start1",
        ),
    )


def tab(label, selected):
    return ScreenElement(
        kind="tabitem",
        label=label,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "uia_tab_scope": "document",
            "uia_document_tab_selected": selected,
        },
    )


class StaticProvider:
    def __init__(self, elements):
        self._elements = tuple(elements)

    def perceive(self, observation):
        return self._elements


def test_perception_engine_exposes_one_active_document():
    scene = PerceptionEngine(
        providers=(
            StaticProvider(
                (
                    tab("Start1", True),
                    tab("OFR/4024-3969-3949N", False),
                    ScreenElement(
                        kind="tabitem",
                        label="Notatka",
                        metadata={
                            "uia_tab_scope": "nested",
                            "uia_document_tab_selected": None,
                        },
                    ),
                )
            ),
        ),
    ).perceive(make_observation())

    assert scene.active_document == "Start1"
    assert scene.metadata["active_document"] == "Start1"
    assert scene.metadata["document_tab_count"] == 2
    assert scene.metadata["selected_document_tab_count"] == 1
    assert scene.metadata["active_document_resolution"] == "resolved"


def test_perception_engine_does_not_guess_active_document_when_selection_is_ambiguous():
    scene = PerceptionEngine(
        providers=(
            StaticProvider(
                (
                    tab("Start1", True),
                    tab("OFR/4024-3969-3949N", True),
                )
            ),
        ),
    ).perceive(make_observation())

    assert scene.active_document is None
    assert scene.metadata["active_document"] is None
    assert scene.metadata["document_tab_count"] == 2
    assert scene.metadata["selected_document_tab_count"] == 2
    assert scene.metadata["active_document_resolution"] == "unresolved"


def test_perception_engine_reports_not_observed_without_document_tabs():
    scene = PerceptionEngine(
        providers=(
            StaticProvider(
                (
                    ScreenElement(
                        kind="tabitem",
                        label="Notatka",
                        metadata={
                            "uia_tab_scope": "nested",
                            "uia_document_tab_selected": None,
                        },
                    ),
                )
            ),
        ),
    ).perceive(make_observation())

    assert scene.active_document is None
    assert scene.metadata["document_tab_count"] == 0
    assert scene.metadata["selected_document_tab_count"] == 0
    assert scene.metadata["active_document_resolution"] == "not_observed"
