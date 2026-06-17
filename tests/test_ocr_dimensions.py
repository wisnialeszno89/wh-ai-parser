from app.core.extractors.dimensions.ocr_dimensions import (
    ocr_dimensions
)


IMAGE = "samples/fix_ru_window.png"

results = ocr_dimensions(
    IMAGE
)

for item in results:

    print(item)