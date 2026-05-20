from PIL import Image


def extract_geometry_region(
    image_path: str,
    output_path: str
):

    image = Image.open(image_path)

    width, height = image.size

    region = (

        width * 0.10,
        0,

        width * 0.90,
        height * 0.65
    )

    cropped = image.crop(region)

    cropped.save(output_path)

    return output_path