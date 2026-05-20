from app.vision.preprocessing.crop_geometry import (
    crop_center_region
)

crop_center_region(
    "samples/zapytanie1.jpg",
    "samples/cropped.jpg"
)

print("DONE")