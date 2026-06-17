from unittest.mock import MagicMock

from app.wh.vision.image_template import (
    ImageTemplate
)

from app.wh.vision.image_template_registry import (
    ImageTemplateRegistry
)


def test_image_template_registry():

    loader = MagicMock()

    loader.load.return_value = (

        ImageTemplate(

            name="add_button",

            image=None

        )

    )

    registry = ImageTemplateRegistry(

        loader

    )

    template = registry.get(

        "add_button"

    )

    assert template.name == (

        "add_button"

    )

    loader.load.assert_called_once_with(

        "add_button"

    )