"""No desktop actions are executed by plan-only offer tests."""
from tools.run_windowhub_sales_offer_live import main


def test_plan_only_limi_with_requested_finishes(capsys):
    rc = main([
        "--customer-name", "Limi Fensterbau",
        "--width", "1500", "--height", "1400", "--quantity", "1",
        "--color-outside", "antracyt", "--color-inside", "biały",
        "--glazing-panes", "2",
    ])
    output = capsys.readouterr().out
    assert rc == 0
    assert "MISSION_CUSTOMER=Limi Fensterbau" in output
    assert "MISSION_COLORS=antracyt / biały" in output
    assert "MISSION_GLAZING_PANES=2" in output
    assert "construction_visible;installation_hidden;removal_hidden;finishing_hidden" in output
    assert "PLAN_ONLY=True" in output


def test_invalid_customer_name_stops_without_desktop_access():
    assert main(["--customer-name", ""]) == 2


def test_invalid_dimensions_stops_without_desktop_access():
    import pytest
    with pytest.raises(ValueError):
        main(["--customer-name", "Limi Fensterbau", "--width", "0"])


def test_sales_add_delegates_to_verified_mdi_action_for_the_exact_offer(monkeypatch):
    from tools import run_navimind_whokna_first_verified_step as acceptance
    from tools.run_windowhub_sales_offer_live import open_verified_position
    from app.agent.runtime import windowhub_goal_v2_coordinator as coordinator

    loop, scene, scoped, action = object(), object(), object(), object()
    calls = []
    monkeypatch.setattr(acceptance, "prepare_add_action", lambda scene: (scoped, action, "OFR/42 <>"))
    monkeypatch.setattr(coordinator, "execute_v2_step", lambda *args, **kwargs: calls.append((args, kwargs)))
    assert open_verified_position(loop, scene)
    assert calls == [((loop, scoped, action), {"expected_offer": "OFR/42 <>"})]


def test_resume_mode_does_not_open_a_new_offer_from_document(monkeypatch, capsys):
    from types import SimpleNamespace as NS
    from tools import run_windowhub_sales_offer_live as sales
    from app.agent.runtime import windowhub_window_activation as activation
    from app.agent.runtime import windows_desktop_agent_control_loop as controls

    monkeypatch.setattr(sales, "os", NS(
        name="nt", environ={"WH_REAL_WINDOWHUB": "1", "COMPUTER_USE_LIVE": "1"},
    ))
    monkeypatch.setattr(activation, "activate_windowhub_workflow_window", lambda: (True, "ok"))
    observed = NS(observation=NS(state=NS(active_application="Okna.exe", active_window_title="Okna - OFR/42-")))
    monkeypatch.setattr(controls, "create_windows_desktop_agent_control_loop",
                        lambda: NS(observe_scene=lambda: observed))
    assert sales.main(["--customer-name", "Test", "--resume-open-wizard", "--execute-live"]) == 4
    assert "MISSION_STOP=expected_already_open_wizard" in capsys.readouterr().out


def test_catalog_accepts_direct_editor_after_verified_glazing(monkeypatch, capsys):
    from types import SimpleNamespace as NS
    from app.agent.runtime import windowhub_catalog_continuation as catalog
    from tools import run_windowhub_top_trans_single_window_mission as native

    def scene(title):
        return NS(observation=NS(state=NS(active_application="Okna.exe", active_window_title=title)))

    observations = iter([scene("Parametry szklenia"), scene("Modyfikator")])
    monkeypatch.setattr(native, "inspect", lambda loop: next(observations))
    monkeypatch.setattr(native, "advance_known_wizard", lambda *args, **kwargs: True)
    monkeypatch.setattr(catalog, "exact_selected", lambda *args: True)
    monkeypatch.setattr(catalog, "catalog_options_for", lambda **kwargs: (("Antracyt / Biały",), ("2 szyby",)))

    assert catalog.continue_to_construction(
        object(), width=1500, height=1400,
        color_outside="antracyt", color_inside="biały", glazing_panes=2,
    ) == 0
    output = capsys.readouterr().out
    assert "GLAZING_PACKAGE_VERIFIED=True" in output
    assert "MODIFIER_REACHED=True" in output
    assert "DRAFT_SAVED_VERIFIED=False" in output
