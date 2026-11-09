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
