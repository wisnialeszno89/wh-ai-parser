from app.wh.vision.image_loader import (
    ImageLoader
)


def test_image_loader():

    loader = ImageLoader()

    image = loader.load(

        "profile_combobox.png"

    )

    assert image.file_name == (

        "profile_combobox.png"

    )

    assert image.size.width == 300

    assert image.size.height == 50