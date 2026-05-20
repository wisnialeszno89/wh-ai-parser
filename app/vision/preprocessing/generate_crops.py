from pathlib import Path

from PIL import Image


def generate_crops(
    image_path: str,
    output_dir: str = "app/vision/debug"
):

    image = Image.open(image_path)

    width, height = image.size

    Path(output_dir).mkdir(
        parents=True,
        exist_ok=True
    )

    crops = []

    regions = {

        "center": (
            width * 0.15,
            height * 0.15,
            width * 0.85,
            height * 0.85
        ),

        "left_focus": (
            0,
            height * 0.10,
            width * 0.70,
            height * 0.90
        ),

        "upper_middle": (
            width * 0.10,
            0,
            width * 0.90,
            height * 0.65
        ),

        "geometry_focus": (
            width * 0.05,
            height * 0.20,
            width * 0.95,
            height * 0.75
        )
    }

    for name, region in regions.items():

        cropped = image.crop(region)

        output_path = (
            f"{output_dir}/{name}.jpg"
        )

        cropped.save(output_path)

        crops.append(output_path)

    return crops