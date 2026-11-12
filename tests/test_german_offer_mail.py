import pytest

from app.agent.intake.german_offer_mail import inspect_german_offer_mail


def test_mail_keeps_door_and_window_separate_and_only_proposes_window_variants():
    text = (
        "Bitte um Angebot\n\nHaustür DL\nWeiss/weiss\n"
        "Wie immer mit Stange und standardfüllug\n950 x 2070\nFenster 1500x1000"
    )
    door, window = inspect_german_offer_mail(text)

    assert door["product_type"] == "entrance_door"
    assert (door["width_mm"], door["height_mm"]) == (950, 2070)
    assert (door["color_inside"], door["color_outside"]) == ("white", "white")
    assert door["source_lines"][0] == "Haustür DL"
    assert "Wie immer mit Stange und standardfüllug" in door["source_lines"]
    assert not door["proposed_variants"]

    assert window["product_type"] == "window"
    assert (window["width_mm"], window["height_mm"]) == (1500, 1000)
    assert window["color_inside"] is None
    assert window["quantity"] is None
    assert window["profile"] is None
    assert window["proposed_variants"] == (
        "Dwa skrzydła, słupek ruchomy",
        "Dwa skrzydła, słupek stały",
    )


@pytest.mark.parametrize(
    "text",
    [
        "Fenster 1499x1000",
        "Fenster 1500x1000 Festverglasung",
        "Fenster 1500x1000 cm",
        "Fenster -1500x1000",
        "Fenster 1500x1000\n1200x900",
    ],
)
def test_proposals_are_limited_to_the_reviewed_unspecified_window(text):
    (window,) = inspect_german_offer_mail(text)
    assert not window["proposed_variants"]


@pytest.mark.parametrize(("label", "code", "mode", "direction"), [
    ("Fenster DKR", "DKR", "tilt_turn", "RIGHT"),
    ("Fenster RUP", "DKR", "tilt_turn", "RIGHT"),
    ("Fenster RUL", "DKL", "tilt_turn", "LEFT"),
    ("Fenster R", "DKR", "tilt_turn", "RIGHT"),
    ("Fenster L", "DKL", "tilt_turn", "LEFT"),
    ("Fenster RU", "RU", "tilt_turn", None),
    ("Fenster Kipp", None, "tilt", None),
    ("Haustür L", "DL", "turn", "LEFT"),
    ("Haustür R", "DR", "turn", "RIGHT"),
    ("Haustür DL", "DL", "turn", "LEFT"),
])
def test_opening_shorthand_follows_product_conventions(label, code, mode, direction):
    (position,) = inspect_german_offer_mail(label + " 1 Stk. 1000 x 2000 mm")

    assert position["opening"] == code
    assert position["opening_spec"] == {"type": mode, "direction": direction}
