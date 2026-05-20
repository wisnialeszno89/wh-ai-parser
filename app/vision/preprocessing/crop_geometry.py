from PIL import Image


def crop_center_region(
    image_path: str,
    output_path: str
):

    image = Image.open(image_path)

    width, height = image.size

    left = width * 0.05
    top = height * 0.05

    right = width * 0.95
    bottom = height * 0.95

    cropped = image.crop(
        (left, top, right, bottom)
    )

    cropped.save(output_path)

    return output_path