from app.vision.preprocessing.detect_vertical_splits import (
    detect_vertical_splits
)

splits = detect_vertical_splits(
    "samples/geometry_region.jpg"
)

print("\nSPLITS:")
print(splits)

print("\nCOUNT:")
print(len(splits))