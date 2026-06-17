from unittest.mock import patch

import numpy as np

from app.wh.vision.image_template_loader import (
    ImageTemplateLoader
)


@patch(
    "cv2.imread"
)
def test_image_template_loader(

    mock_imread

):

    mock_imread.return_value = np.zeros(

        (

            40,

            100,

            3

        ),

        dtype=np.uint8

    )

    loader = ImageTemplateLoader()

    template = loader.load(

        "add_button.png"

    )

    assert template.name == (

        "add_button.png"

    )

    assert template.image.shape == (

        40,

        100,

        3

    )