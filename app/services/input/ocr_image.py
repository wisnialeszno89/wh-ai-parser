import pytesseract

from PIL import Image

from app.services.input.image_preprocess import (
    preprocess_image
)


def extract_text_from_image(
    image_path: str
):

    processed_path = (
        "samples/processed.png"
    )


    preprocess_image(

        image_path,

        processed_path
    )


    image = Image.open(
        processed_path
    )


    text = pytesseract.image_to_string(

        image,

        lang="pol"
    )


    return text