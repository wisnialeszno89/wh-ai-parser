from app.vision.preprocessing.split_segments import (
    split_segments
)

from app.vision.services.classify_segment_service import (
    classify_segment
)

segments = split_segments(
    "samples/geometry_region.jpg"
)

for s in segments:

    result = classify_segment(s)

    print("\n")
    print(s)
    print(result)