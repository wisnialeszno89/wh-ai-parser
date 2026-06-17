import numpy as np

from app.wh.runtime.vision.image_adapter import (
    ImageAdapter
)


def test_image_adapter():

    adapter = (

        ImageAdapter()

    )

    image = [

        [

            1,

            2

        ],

        [

            3,

            4

        ]

    ]

    result = (

        adapter.to_array(

            image

        )

    )

    assert isinstance(

        result,

        np.ndarray

    )

    assert result.shape == (

        2,

        2

    )