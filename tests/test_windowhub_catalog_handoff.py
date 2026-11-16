"""Salesperson approval handoff and screen-efficient catalog policy tests."""
from types import SimpleNamespace as N

from app.agent.runtime.windowhub_catalog_continuation import catalog_options_for
from app.agent.runtime.windowhub_catalog_handoff import teach_and_resume


def test_default_catalog_options_are_exact_and_two_sided(monkeypatch, tmp_path):
    from app.agent.learning import windowhub_catalog_memory as memory
    monkeypatch.setattr(memory, "default_skill_file", lambda: tmp_path / "no_skills.json")
    colors, glazing = catalog_options_for(
        outside="antracyt", inside="biały", glazing_panes=2
    )
    assert "Antracyt / Biały" in colors
    assert "Dwuszybowy" in glazing
    assert "Antracyt / Antracyt" not in colors


def test_taught_catalog_handoff_continues_only_after_approval(monkeypatch):
    from tools import run_windowhub_top_trans_single_window_mission as legacy
    from app.agent.runtime import windowhub_catalog_handoff as handoff
    from app.agent.runtime import windowhub_window_activation as activation
    monkeypatch.setattr(activation, "activate_windowhub_workflow_window", lambda: (True, "mock_refocus"))
    labels = ["gotowe", "tak", "nie", "tak"]
    scene = N(observation=N(state=N(
        active_application="Okna.exe", active_window_title="Podstawowe parametry okna"
    )))
    monkeypatch.setattr(legacy, "inspect", lambda loop: scene)
    monkeypatch.setattr(handoff, "current_catalog_value", lambda s, f: "RAL 7016 / biały")
    monkeypatch.setattr(
        handoff, "record_skill",
        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("saving declined"))
    )
    result = teach_and_resume(
        object(), field="profile_color", key="antracyt|biały",
        stage="basic_parameters", meaning="zewnątrz antracyt, wewnątrz biały",
        ask=lambda prompt: labels.pop(0),
    )
    assert result is scene
    assert labels == []


def test_taught_catalog_handoff_requires_resume_permission(monkeypatch):
    from tools import run_windowhub_top_trans_single_window_mission as legacy
    from app.agent.runtime import windowhub_catalog_handoff as handoff
    scene = N(observation=N(state=N(
        active_application="Okna.exe", active_window_title="Parametry szklenia"
    )))
    monkeypatch.setattr(legacy, "inspect", lambda loop: scene)
    monkeypatch.setattr(handoff, "current_catalog_value", lambda s, f: "2 szyby")
    answers = iter(["gotowe", "tak", "nie", "nie"])
    assert teach_and_resume(
        object(), field="glazing_package", key="2", stage="glazing",
        meaning="2 szyby", ask=lambda prompt: next(answers)
    ) is None


def test_hardware_handoff_requires_editor_readback_and_resume(monkeypatch):
    from app.agent.runtime.windowhub_catalog_continuation import continue_to_construction
    from tools import run_windowhub_top_trans_single_window_mission as legacy
    from app.agent.runtime import windowhub_window_activation as activation
    monkeypatch.setattr(activation, "activate_windowhub_workflow_window", lambda: (True, "mock_refocus"))

    hardware = N(observation=N(state=N(
        active_application="Okna.exe", active_window_title="Parametry okuć"
    )))
    modifier = N(observation=N(state=N(
        active_application="Okna.exe", active_window_title="Modyfikator"
    )))
    visited = [hardware, modifier, modifier]
    monkeypatch.setattr(legacy, "inspect", lambda loop: visited.pop(0))
    answers = iter(["gotowe", "tak"])
    assert continue_to_construction(
        object(), width=1500, height=1400,
        color_outside="antracyt", color_inside="biały",
        glazing_panes=2, interactive_handoff=True,
        ask=lambda prompt: next(answers),
    ) == 0
    assert not visited


def test_hardware_without_handoff_is_not_claimed_as_editor(monkeypatch):
    from app.agent.runtime.windowhub_catalog_continuation import continue_to_construction
    from tools import run_windowhub_top_trans_single_window_mission as legacy
    hardware = N(observation=N(state=N(
        active_application="Okna.exe", active_window_title="Parametry okuć"
    )))
    monkeypatch.setattr(legacy, "inspect", lambda loop: hardware)
    assert continue_to_construction(
        object(), width=1500, height=1400,
        color_outside="antracyt", color_inside="biały",
        glazing_panes=2, interactive_handoff=False
    ) == 4
