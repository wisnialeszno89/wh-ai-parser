from types import SimpleNamespace as NS

from tools import run_windowhub_existing_offer_position_test as mission


def scene(title, *, hwnd=200, elements=()):
    return NS(observation=NS(
        state=NS(active_application="Okna.exe", active_window_title=title),
        metadata={"window_handle": hwnd},
    ), elements=elements)


def button(label, automation_id="12325"):
    return NS(kind="button", label=label, metadata={
        "source": "windows_ui_automation", "automation_id": automation_id,
        "uia_visible": True, "uia_enabled": True,
    })


def native_owner(title):
    return NS(foreground=lambda: 200, parent=lambda hwnd, kind: 100, title=lambda hwnd: title)


def test_resume_requires_window_owner_of_requested_offer():
    wizard = scene("Podstawowe parametry okna")
    assert mission.belongs_to_offer(wizard, "OFR/42-", native_owner("Okna - OFR/42 <>"))
    assert not mission.belongs_to_offer(wizard, "OFR/42-", native_owner("Okna - OFR/42-99 <>"))
    assert not mission.belongs_to_offer(wizard, "OFR/42-", native_owner("Okna - ZLC/42"))


def test_finish_confirms_only_one_button_then_observes_editor(monkeypatch):
    calls = []
    before = scene("Parametry szklenia", elements=(button("Zakończ"),))
    after = scene("Modyfikator")
    monkeypatch.setattr(mission, "resolve_native_wrapper", lambda *args, **kwargs: NS(
        iface_invoke=NS(Invoke=lambda: calls.append(kwargs)),
    ))
    monkeypatch.setattr(mission, "inspect", lambda loop: after)
    assert mission.confirm_stage(object(), before, "OFR/42-", native_owner("Okna - OFR/42-")) is after
    assert calls == [{"label": "Zakończ", "automation_id": "12325", "allowed_stages": ("glazing",)}]


def test_ambiguous_confirmation_blocks_without_input(monkeypatch):
    before = scene("Podstawowe parametry okna", elements=(button("OK"), button("Zakończ", "999")))
    monkeypatch.setattr(mission, "resolve_native_wrapper", lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("resolver called for ambiguous buttons"),
    ))
    assert mission.confirm_stage(object(), before, "OFR/42-", native_owner("Okna - OFR/42-")) is None


def test_cli_asks_once_for_offer_and_never_for_customer(monkeypatch, capsys):
    from app.agent.runtime import windows_desktop_agent_control_loop as controls

    monkeypatch.setattr(mission, "os", NS(
        name="nt", environ={"COMPUTER_USE_LIVE": "1", "WH_REAL_WINDOWHUB": "1"},
    ))
    asked = []
    monkeypatch.setattr("builtins.input", lambda prompt: asked.append(prompt) or "OFR/42-")
    monkeypatch.setattr(controls, "create_windows_desktop_agent_control_loop", object)
    monkeypatch.setattr(mission, "_Win32Mdi", object)
    monkeypatch.setattr(mission, "run", lambda loop, offer, api: 0 if offer == "OFR/42-" else 4)
    assert mission.main(["--execute-live", "--start-delay", "0"]) == 0
    assert len(asked) == 1 and "OFR" in asked[0]


def test_test_catalog_choice_verifies_the_exact_observed_label(monkeypatch, capsys):
    before, after = scene("Podstawowe parametry okna"), scene("Podstawowe parametry okna")
    selected = []

    def select(observed, **kwargs):
        assert observed is before
        assert kwargs["allow_test_catalog_choice"] is True
        selected.append("9001 Kremowy")
        return selected[0]

    monkeypatch.setattr(mission, "select_catalog_label_once", select)
    monkeypatch.setattr(mission, "inspect", lambda loop: after)
    monkeypatch.setattr(mission, "exact_selected", lambda observed, field, options: (
        observed is after and options == ("9001 Kremowy",)
    ))
    assert mission.choose_catalog(
        object(), before, "OFR/42-", native_owner("Okna - OFR/42-"),
        "profile_color", ("Antracyt / Biały",),
    ) is after
    assert selected == ["9001 Kremowy"]
    assert "TEST_CATALOG_READBACK=profile_color:'9001 Kremowy'" in capsys.readouterr().out


def test_exact_sales_catalog_policy_does_not_substitute_test_labels():
    from tools.run_windowhub_top_trans_single_window_mission import _catalog_choice

    options = ["<Wybierz>", "brak", "Biały", "BIAŁY", "9001 Kremowy", "7016 Antracyt"]
    assert _catalog_choice(options, {"antracyt / biały"}) is None
    assert _catalog_choice(options, {"antracyt / biały"}, allow_test_catalog_choice=True) == 4
    assert _catalog_choice(options, {"7016 antracyt"}, allow_test_catalog_choice=True) == 5


def test_combo_readback_prefers_selected_text_to_control_caption():
    from app.agent.perception.windowhub_ui_automation_provider import WindowHubUIAutomationProvider

    combo = NS(
        element_info=NS(control_type="ComboBox"),
        selected_text=lambda: "9001 Kremowy",
        window_text=lambda: "Wybierz kolor profili",
    )
    assert WindowHubUIAutomationProvider._current_control_value(combo) == "9001 Kremowy"


def test_basic_parameters_prefers_known_next_when_finish_is_also_visible(monkeypatch):
    calls = []
    before = scene("Podstawowe parametry okna", elements=(
        button("Dalej >", "12324"), button("Zakończ"),
    ))
    after = scene("Parametry szklenia")
    monkeypatch.setattr(mission, "resolve_native_wrapper", lambda *args, **kwargs: NS(
        iface_invoke=NS(Invoke=lambda: calls.append(kwargs["label"])),
    ))
    monkeypatch.setattr(mission, "inspect", lambda loop: after)
    assert mission.confirm_stage(object(), before, "OFR/42-", native_owner("Okna - OFR/42-")) is after
    assert calls == ["Dalej >"]


def test_finish_waits_when_the_old_snapshot_has_already_lost_focus(monkeypatch):
    before = scene("Podstawowe parametry okna", elements=(button("Zakończ"),))
    after = scene("Modyfikator", hwnd=201)
    hwnd = [200]
    calls = []
    api = native_owner("Okna - OFR/42-")
    api.foreground = lambda: hwnd[0]

    def invoke():
        calls.append("finish")
        hwnd[0] = 201

    observations = iter((before, after))
    monkeypatch.setattr(mission, "inspect", lambda loop: next(observations))
    monkeypatch.setattr(mission.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(mission, "resolve_native_wrapper", lambda *args, **kwargs: NS(
        iface_invoke=NS(Invoke=invoke),
    ))

    assert mission.confirm_stage(object(), before, "OFR/42-", api) is after
    assert calls == ["finish"]


def test_from_start_runs_only_on_the_offer_confirmed_by_document_core(monkeypatch):
    from app.agent.runtime import windowhub_document_core as document
    from tools import run_windowhub_new_offer_entry as entry

    calls = []
    start = scene("Okna - Start1")
    wizard = scene("Dodawanie nowej pozycji")
    api = native_owner("Okna - OFR/42 <>")
    monkeypatch.setattr(mission, "inspect", lambda loop: start)
    monkeypatch.setattr(entry, "main", lambda args: calls.append(("new_offer", args)) or 0)

    def setup(*, customer_name, fresh_document, on_confirmed, confirm_similar_customer, replace_customer_filter, allow_test_blank_customer):
        assert confirm_similar_customer and not replace_customer_filter and allow_test_blank_customer
        calls.append(("setup", customer_name, fresh_document))
        on_confirmed(wizard)
        return 0

    monkeypatch.setattr(document, "run_document_core", setup)
    monkeypatch.setattr(mission, "run", lambda loop, offer, api, **kwargs: (
        calls.append(("position", offer, kwargs)) or 0
    ))

    assert mission.run_from_start(object(), "Test", api) == 0
    assert calls == [
        ("new_offer", ["--execute-live"]),
        ("setup", "Test", True),
        ("position", "OFR/42 <>", {"stop_at_editor": True, "color_label": None}),
    ]


def test_from_start_refuses_to_create_offer_if_a_wizard_is_open(monkeypatch):
    monkeypatch.setattr(mission, "inspect", lambda loop: scene("Podstawowe parametry okna"))
    assert mission.run_from_start(object(), "Test", native_owner("Okna - OFR/42-")) == 4


def test_new_offer_uses_verified_start1_navigation_from_an_open_offer(monkeypatch):
    from tools import run_windowhub_new_offer_entry as entry

    monkeypatch.setattr(mission, "inspect", lambda loop: scene("Okna - OFR/42-"))
    calls = []
    monkeypatch.setattr(entry, "main", lambda args: calls.append(args) or 4)
    assert mission.run_from_start(object(), "Test", native_owner("Okna - OFR/42-")) == 4
    assert calls == [["--execute-live"]]


def test_requested_glazing_is_an_exact_build_up_not_just_a_pane_count():
    from tools.run_windowhub_top_trans_single_window_mission import _catalog_choice

    options = ["3 szyby", "4/16/4/16/4", "Pakiet szybowy: 4 / 12 / 4 / 12 / 4 mm"]
    assert _catalog_choice(options, set(), match_label=mission.matches_required_glazing) == 2
    assert _catalog_choice(options + ["4-12-4-12-4"], set(),
                           match_label=mission.matches_required_glazing) is None
    assert not mission.matches_required_glazing("44/12/4/12/4")
    assert not mission.matches_required_glazing("4/12/4/12/44")
