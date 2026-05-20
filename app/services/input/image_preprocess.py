from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps


def preprocess_image(
    image_path: str,

    output_path: str
):

    image = Image.open(
        image_path
    )


    image = image.convert(
        "L"
    )


    image = ImageOps.autocontrast(
        image
    )


    image = image.filter(
        ImageFilter.SHARPEN
    )


    threshold = 160


    image = image.point(

        lambda p:

        255

        if p > threshold

        else 0
    )


    image.save(
        output_path
    )


    return output_path