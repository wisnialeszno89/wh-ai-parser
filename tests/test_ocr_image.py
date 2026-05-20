from pathlib import Path

from app.services.input.ocr_image import (
    extract_text_from_image
)


samples = list(

    Path("samples").glob("*")
)


if not samples:

    raise ValueError(
        "No files in samples/"
    )


image_path = str(
    samples[0]
)


print()
print("IMAGE:")
print(image_path)


text = extract_text_from_image(
    image_path
)


print()
print("========== OCR ==========")
print()

print(text)