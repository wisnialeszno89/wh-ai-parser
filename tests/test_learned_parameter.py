from app.agent.learning.learned_parameter import (
    LearnedParameterBinder,
    canonical_parameter_name,
)
from app.agent.learning.learned_workflow import LearnedAction


def test_canonical_parameter_name_normalizes_polish_semantic_label():
    assert canonical_parameter_name("Szerokość") == "szerokosc"
    assert canonical_parameter_name("Kolor od środka") == "kolor_od_srodka"


def test_binder_overrides_parameterized_demo_value():
    action = LearnedAction(
        name="write_text",
        target="Szerokość",
        value="1200",
        value_source="parameter",
        parameter_name="szerokosc",
    )

    bound = LearnedParameterBinder().bind(
        action,
        {"width": 1350, "Szerokość": 1400},
    )

    assert bound.value == "1400"
    assert bound.parameter_name == "szerokosc"


def test_binder_preserves_demo_value_when_parameter_is_missing():
    action = LearnedAction(
        name="write_text",
        target="Szerokość",
        value="1200",
        value_source="parameter",
        parameter_name="szerokosc",
    )

    bound = LearnedParameterBinder().bind(
        action,
        {"height": 1500},
    )

    assert bound.value == "1200"


def test_binder_allows_explicit_empty_parameter_value():
    action = LearnedAction(
        name="write_text",
        target="Opis",
        value="stary",
        value_source="parameter",
        parameter_name="opis",
    )

    bound = LearnedParameterBinder().bind(
        action,
        {"opis": ""},
    )

    assert bound.value == ""
