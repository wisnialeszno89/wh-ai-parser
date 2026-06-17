from pprint import pprint

from app.ui.agent.pattern_to_operations import (
    build_operations_from_pattern
)


patterns = [

    "single_sash",

    "double_sash",

    "fix_plus_sash",

    "sash_plus_fix"
]


for pattern in patterns:

    print()

    print("=" * 80)
    print(pattern)
    print("=" * 80)

    operations = (

        build_operations_from_pattern(
            pattern
        )
    )

    for op in operations:

        pprint(op)

    print()