from unittest.mock import MagicMock

from app.wh.vision.image_template_registry import (
    ImageTemplateRegistry
)


def test_image_template_registry_groups():

    loader = MagicMock()

    registry = ImageTemplateRegistry(

        loader

    )

    registry.get_all(

        "frame"

    )

    assert (

        loader.load.call_count

        == 3

    )