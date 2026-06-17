from pprint import pprint

from app.ui.agent.schema_to_operations import (
    schema_to_operations
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

operations = (

    schema_to_operations(
        construction
    )
)

print()

print("=" * 80)
print("SCHEMA TO OPERATIONS")
print("=" * 80)

print()

for op in operations:

    pprint(op)

print()