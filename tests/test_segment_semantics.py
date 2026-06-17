from pprint import pprint

from app.ui.agent.segment_semantics import (
    enrich_segments
)

construction = {

    "segments": [

        {
            "opening":
                "tilt_turn"
        },

        {
            "opening":
                "fixed"
        }
    ]
}

segments = enrich_segments(
    construction
)

print()

print("=" * 80)
print("SEGMENTS")
print("=" * 80)

print()

for segment in segments:

    pprint(segment)

print()