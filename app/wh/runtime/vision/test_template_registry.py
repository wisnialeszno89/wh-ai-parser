from app.wh.runtime.vision.template_registry import (
    TemplateRegistry
)


def test_template_registry():

    registry = (

        TemplateRegistry()

    )

    templates = (

        registry.get_templates(

            "frame"

        )

    )

    assert len(

        templates

    ) == 3

    assert (

        "frame_button.png"

        in templates

    )