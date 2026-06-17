import numpy as np

from app.wh.runtime.vision.template_loader import (
    TemplateLoader
)


def test_template_loader():

    loader = (

        TemplateLoader()

    )

    result = (

        loader.load(

            "frame_button.png"

        )

    )

    assert isinstance(

        result,

        np.ndarray

    )

    assert result.shape == (

        50,

        50,

        3

    )