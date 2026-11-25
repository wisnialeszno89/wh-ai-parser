"""Offline checks for opt-in human demonstration learning (no Windows input)."""
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.navimind_local_teaching_session import LocalTeachingSession
from app.agent.runtime.navimind_panel_controller import NaviMindPanelController, PanelMode


def observed(title, *, checked=False, app="Okna.exe", secret="KLIENT 1456"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application=app, active_window_title=title,
            ),
        ),
        elements=(
            ScreenElement(kind="checkbox", label="OknaWPF", metadata={
                "source": "windowhub_ui_automation",
                "uia_visible": True, "uia_enabled": True,
                "uia_checked": checked,
                "automation_id": "IDC_CENA_OKNA",
                "current_value": secret,
                "semantic_label": "Bez ceny konstrukcji",
            }),
        ),
    )


def test_manual_learning_is_opt_in_and_never_records_customer_values():
    session = LocalTeachingSession()
    assert not session.observe(observed("Właściwości dokumentu"))
    assert session.experience() == ()
    assert session.start()
    assert not session.observe(observed("Właściwości dokumentu", checked=False))
    assert session.observe(observed("Właściwości dokumentu", checked=True))
    summary = session.finish()
    assert summary["record_count"] == 1
    experience = session.experience()
    assert len(experience) == 1
    assert experience[0]["certainty"] == "observed_effect_not_causal_action"
    assert "KLIENT" not in str(experience)
    assert "IDC_CENA_OKNA" not in str(experience)
    assert "1456" not in str(experience)


def test_external_app_is_never_recorded_or_joined_to_windowhub_sequence():
    session = LocalTeachingSession()
    session.start()
    assert not session.observe(observed("Okna - Start1"))
    assert not session.observe(observed("Mail klienta", app="outlook.exe"))
    assert not session.observe(observed("Właściwości dokumentu"))
    assert session.finish()["record_count"] == 0


def test_teaching_capacity_is_bounded_without_restarting_or_losing_history():
    session = LocalTeachingSession(max_records=2)
    session.start()
    assert not session.observe(observed("Właściwości dokumentu", checked=False))
    assert session.observe(observed("Właściwości dokumentu", checked=True))
    assert session.observe(observed("Właściwości dokumentu", checked=False))
    for i in range(6):
        session.observe(observed("Właściwości dokumentu", checked=bool(i % 2)))
    assert session.active
    assert session.finish()["record_count"] == 2
    assert len(session.experience()) <= 2


def test_training_button_toggles_without_granting_input_permit():
    panel = NaviMindPanelController()
    started = panel.training()
    assert started.mode == PanelMode.LEARNING and started.human_controls
    assert started.can_learn
    assert panel.current_permit() is None
    stopped = panel.training()
    assert stopped.mode == PanelMode.HUMAN and stopped.human_controls
    assert panel.current_permit() is None


def test_learning_discard_removes_all_model_advisory_data():
    session = LocalTeachingSession()
    session.start()
    session.observe(observed("Okna - Start1"))
    session.observe(observed("Właściwości dokumentu"))
    assert session.finish()["record_count"] == 1
    assert session.experience()
    session.discard()
    assert not session.active
    assert not session.experience()
