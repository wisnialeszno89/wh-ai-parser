from app.wh.vision.image import (
    Image
)

from app.wh.vision.image_size import (
    ImageSize
)


def test_image():

    image = Image(

        file_name="profile_combobox.png",

        size=ImageSize(

            width=300,

            height=50

        )

    )

    assert image.file_name == (

        "profile_combobox.png"

    )

    assert image.size.width == 300

    assert image.size.height == 50