import os

import pytest

from tools.visual_offer_lab import CUSTOMER, offer_verifier, read_dimensions, save_state


def test_verifier_requires_a_saved_draft_from_the_current_session(tmp_path):
    path = tmp_path / "lab.json"
    verify = offer_verifier(path, "session", os.getpid())
    draft = dict(customer=CUSTOMER, installation=True, quantity=2, width=1500, height=1400)

    assert not verify()
    save_state(path, "session", None)
    assert not verify()
    save_state(path, "old-session", draft)
    assert not verify()

    for wrong in (
        dict(customer="Klient Testowy"),
        dict(installation=False),
        dict(quantity=1),
        dict(width=1400, height=1500),
        dict(width=1500.0),
    ):
        save_state(path, "session", draft | wrong)
        assert not verify()

    save_state(path, "session", draft)
    assert verify()
    assert not offer_verifier(path, "session", os.getpid() + 1)()
    path.write_text("[]", encoding="utf-8")
    assert not verify()


@pytest.mark.parametrize("width", ["", "0", "-5", "1500.0", "１５００", "12345"])
def test_dimensions_reject_invalid_input(width):
    with pytest.raises(ValueError):
        read_dimensions(("2", width, "1400"))


def test_dimensions_preserve_width_and_height_order():
    assert read_dimensions(iter(("2", " 1500 ", "1400"))) == (2, 1500, 1400)


def test_document_verifier_requires_exact_customer_prices_and_ok(tmp_path):
    from tools.visual_offer_lab import DOCUMENT_TITLE, document_verifier

    path = tmp_path / "document.json"
    check = document_verifier(path, "session", os.getpid())
    valid = dict(customer="Top Trans", confirmed=True, construction=False,
                 installation=True, removal=True, finishing=True)
    for change in (
        {"customer": "Top Trans S.A."}, {"confirmed": False}, {"construction": True},
        {"installation": False}, {"removal": False}, {"finishing": False},
        {"finishing": 1},
    ):
        save_state(path, "session", valid | change, title=DOCUMENT_TITLE)
        assert not check()

    save_state(path, "session", valid)
    assert not check()
    save_state(path, "session", valid, title=DOCUMENT_TITLE)
    assert check()


def test_document_start_rejects_already_edited_and_confirmed_sessions(tmp_path):
    import json

    from tools.visual_offer_lab import DOCUMENT_TITLE, document_start_ready

    path = tmp_path / "document.json"

    def saved_state(draft=None, *, ready=False, title=DOCUMENT_TITLE):
        save_state(path, "session", draft, title=title, document_ready=ready)
        return json.loads(path.read_text(encoding="utf-8"))

    assert document_start_ready(saved_state(ready=True))
    assert not document_start_ready(saved_state())
    assert not document_start_ready(saved_state({"confirmed": True}, ready=True))
    assert not document_start_ready(saved_state(ready=True, title="NaviMind Visual Offer Lab"))
    assert not document_start_ready({"title": DOCUMENT_TITLE, "document_ready": True})


def test_document_observer_reports_selected_customer_and_live_states(tmp_path):
    from tools.visual_offer_lab import DOCUMENT_TITLE, document_observer

    path = tmp_path / "document.json"
    observe = document_observer(path, "session", os.getpid())
    snapshot = dict(customer="Top Trans S.A.", construction=True,
                    installation=False, removal=False, finishing=False)
    save_state(path, "session", None, title=DOCUMENT_TITLE, document_snapshot=snapshot)
    assert "Zaznaczony klient: Top Trans S.A.." in observe()
    save_state(path, "session", None, title=DOCUMENT_TITLE,
               document_snapshot=snapshot | {"customer": "Top Trans"})
    assert "Zaznaczony klient: Top Trans." in observe()
    assert "Bez ceny montażu: odznaczone" in observe()
    assert "Formularz po OK: nie" in observe()
    assert document_observer(path, "different", os.getpid())() is None


def test_document_points_map_logical_widget_positions_to_cropped_image_pixels():
    from types import SimpleNamespace

    from PIL import Image

    from tools.visual_offer_lab import document_image_points

    frame = SimpleNamespace(
        image=Image.new("RGB", (400, 200)),
        token=SimpleNamespace(window_box=(125, 125, 1125, 750), view_box=(100, 150, 500, 350)),
    )
    snapshot = {"client_size": [800, 500], "points": {
        "Top Trans": [120, 160], "Top Trans S.A.": [120, 140], "offscreen": [50, 200],
    }}
    assert document_image_points(snapshot, frame) == {"Top Trans": (50, 50), "Top Trans S.A.": (50, 25)}


def test_order_verification_requires_document_and_saved_window_from_same_session(tmp_path):
    from tools.visual_offer_lab import ORDER_TITLE, order_verifier

    path = tmp_path / "order.json"
    verify = order_verifier(path, "session", os.getpid())
    document = dict(customer="Top Trans", confirmed=True, construction=False,
                    installation=True, removal=True, finishing=True)
    window = dict(quantity=2, width=1500, height=1400)
    save_state(path, "session", None, title=ORDER_TITLE, document_snapshot=window)
    assert not verify()
    save_state(path, "session", window, title=ORDER_TITLE)
    assert not verify()
    draft = dict(document=document, **window)
    save_state(path, "session", draft | {"width": 1400, "height": 1500}, title=ORDER_TITLE)
    assert not verify()
    save_state(path, "session", draft | {"document": document | {"confirmed": False}}, title=ORDER_TITLE)
    assert not verify()
    save_state(path, "wrong-session", draft, title=ORDER_TITLE)
    assert not verify()
    save_state(path, "session", draft, title=ORDER_TITLE)
    assert verify()


def test_order_observer_describes_position_values_and_focus(tmp_path):
    from tools.visual_offer_lab import ORDER_TITLE, document_observer

    path = tmp_path / "order.json"
    snapshot = dict(stage="pozycja", quantity="2", width="", height="1400", focus="Szerokość (mm)")
    save_state(path, "session", None, title=ORDER_TITLE, document_snapshot=snapshot)
    observation = document_observer(path, "session", os.getpid(), title=ORDER_TITLE)()
    assert "Ilość sztuk = 2" in observation
    assert "Szerokość (mm) = puste" in observation
    assert "Wysokość (mm) = 1400" in observation
    assert "Pole z fokusem: Szerokość (mm)" in observation


def test_order_replace_policy_only_accepts_numeric_focus_in_current_position(tmp_path):
    from tools.visual_offer_lab import ORDER_TITLE, order_numeric_focus

    path = tmp_path / "order.json"
    focused = order_numeric_focus(path, "session", os.getpid())
    snapshot = {"stage": "pozycja", "focus": "Szerokość (mm)"}
    assert not focused()
    save_state(path, "session", None, title=ORDER_TITLE, document_snapshot=snapshot)
    assert focused()
    for change in ({"stage": "podsumowanie"}, {"focus": None}, {"focus": "Klient"}):
        save_state(path, "session", None, title=ORDER_TITLE, document_snapshot=snapshot | change)
        assert not focused()
    save_state(path, "previous-session", None, title=ORDER_TITLE, document_snapshot=snapshot)
    assert not focused()


def test_second_order_has_its_own_goal_observation_and_verification(tmp_path):
    from tools.visual_offer_lab import ORDER_CASES, ORDER_TITLE, document_observer, order_verifier

    path = tmp_path / "order.json"
    case = "baupartner"
    verify = order_verifier(path, "session", os.getpid(), case)
    observe = document_observer(path, "session", os.getpid(), title=ORDER_TITLE)
    goal = ORDER_CASES[case].goal()
    assert "Baupartner Nord" in goal and "1230 mm" in goal and "1780 mm" in goal
    assert "Zaznacz Bez ceny konstrukcji." in goal
    assert "Odznacz Bez ceny montażu." in goal
    snapshot = dict(stage="pozycja", quantity="3", width="", height="", focus="Szerokość (mm)")
    save_state(path, "session", None, title=ORDER_TITLE, document_snapshot=snapshot, order_case=case)
    assert "Wpisz 1230" in observe()
    assert not verify()

    document = dict(customer="Baupartner Nord", confirmed=True, construction=True,
                    installation=False, removal=False, finishing=True)
    draft = dict(document=document, quantity=3, width=1230, height=1780)
    for candidate, stored_case in (
        (draft, "top-trans"),
        (draft | {"width": 1500}, case),
        (draft | {"document": document | {"customer": "Baupartner Nord GmbH"}}, case),
        (draft | {"document": document | {"installation": True}}, case),
    ):
        save_state(path, "session", candidate, title=ORDER_TITLE, order_case=stored_case)
        assert not verify()
    save_state(path, "session", draft, title=ORDER_TITLE, order_case=case)
    assert verify()
    assert not order_verifier(path, "session", os.getpid())()


def test_baupartner_local_position_actions_follow_verified_values_and_focus(tmp_path):
    from types import SimpleNamespace

    from PIL import Image

    from tools.visual_offer_lab import ORDER_TITLE, order_form_action

    path = tmp_path / "order.json"
    case = "baupartner"
    choose = order_form_action(path, "session", os.getpid(), case)
    frame = SimpleNamespace(
        image=Image.new("RGB", (800, 500)),
        token=SimpleNamespace(window_box=(10, 20, 810, 520), view_box=(0, 0, 800, 500)),
    )

    def snapshot(**changes):
        state = dict(stage="pozycja", quantity="3", width="1230", height="", focus="Szerokość (mm)",
                     client_size=[800, 500], points={"height": [100, 320], "review": [80, 360],
                                                     "edit": [50, 140], "save": [70, 110]})
        save_state(path, "session", None, title=ORDER_TITLE, order_case=case,
                   document_snapshot=state | changes)
        return choose(frame)

    assert snapshot(stage="document") is None
    assert snapshot()["y"] == 320
    assert snapshot(focus="Wysokość (mm)")["text"] == "1780"
    assert snapshot(height="1780")["y"] == 360
    assert snapshot(stage="podsumowanie", height=1400, width=1230, quantity=3)["y"] == 140
    assert snapshot(stage="podsumowanie", height=1780, width=1230, quantity=3)["y"] == 110
    assert snapshot(points={})["kind"] == "ask_user"


def test_order_actions_require_exact_customer_and_read_back_each_preference(tmp_path):
    from types import SimpleNamespace

    from PIL import Image

    from tools.visual_offer_lab import ORDER_TITLE, order_form_action

    path = tmp_path / "order.json"
    case = "baupartner"
    choose = order_form_action(path, "session", os.getpid(), case)
    frame = SimpleNamespace(
        image=Image.new("RGB", (800, 500)),
        token=SimpleNamespace(window_box=(10, 20, 810, 520), view_box=(0, 0, 800, 500)),
    )
    points = {"Baupartner Nord": [100, 220], "Baupartner Nord GmbH": [100, 200],
              "construction": [110, 262], "installation": [110, 288],
              "removal": [110, 315], "finishing": [110, 341], "ok": [77, 380]}

    def next_action(**changes):
        snapshot = dict(stage="wlasciwosci", client_size=[800, 500], points=points,
                        customer="Baupartner Nord", construction=True, installation=False,
                        removal=False, finishing=True)
        save_state(path, "session", None, title=ORDER_TITLE, order_case=case,
                   document_snapshot=snapshot | changes)
        return choose(frame)

    assert next_action(customer=None, points={"Baupartner Nord GmbH": [100, 200]}) is None
    assert next_action(customer="Baupartner Nord GmbH")["y"] == 220
    assert next_action(construction=False, installation=True)["y"] == 262
    assert next_action(installation=True)["y"] == 288
    assert next_action(removal=True)["y"] == 315
    assert next_action(finishing=False)["y"] == 341
    assert next_action(installation=None)["kind"] == "ask_user"
    assert next_action()["y"] == 380
