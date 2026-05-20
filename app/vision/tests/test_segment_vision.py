from app.vision.services.segment_vision_service import (
    analyze_segments_from_file
)

from app.vision.parsers.segment_parser import (
    parse_segment_response
)

raw = analyze_segments_from_file(
    "samples/geometry_region.jpg"
)

print("\nRAW:")
print(raw)

parsed = parse_segment_response(
    raw
)

print("\nPARSED:")
print(parsed)