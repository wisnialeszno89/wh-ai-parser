from pprint import pprint

from app.ui.agent.segment_semantics import (
    enrich_segments
)

from app.ui.agent.segment_roles import (
    assign_roles
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

segments = assign_roles(
    segments
)

print()

print("=" * 80)
print("ROLES")
print("=" * 80)

print()

for item in segments:

    pprint(item)

print()