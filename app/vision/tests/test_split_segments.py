from app.vision.preprocessing.split_segments import (
    split_segments
)

results = split_segments(
    "samples/geometry_region.jpg"
)

for r in results:

    print(r)