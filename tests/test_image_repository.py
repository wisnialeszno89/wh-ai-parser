from app.wh.vision.image_repository import (
    ImageRepository
)


def test_image_repository():

    repository = ImageRepository()

    image = repository.get(

        "profile"

    )

    assert image.name == "profile"

    assert (

        image.file_name

        ==

        "profile_combobox.png"

    )