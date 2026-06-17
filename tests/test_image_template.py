import numpy as np

from app.wh.vision.image_template import (
    ImageTemplate
)


def test_image_template():

    image = np.zeros(

        (

            40,

            100,

            3

        ),

        dtype=np.uint8

    )

    template = ImageTemplate(

        name="add_button",

        image=image

    )

    assert template.name == "add_button"

    assert template.image.shape == (

        40,

        100,

        3

    )