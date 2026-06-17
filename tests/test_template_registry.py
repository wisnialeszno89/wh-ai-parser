from app.wh.vision.template_registry import (
    TEMPLATES
)


def test_template_registry():

    assert "profile" in TEMPLATES

    assert (

        TEMPLATES["profile"]

        .image

        ==

        "profile_combobox.png"

    )