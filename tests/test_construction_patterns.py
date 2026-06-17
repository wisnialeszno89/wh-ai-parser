from app.ui.agent.construction_patterns import (
    detect_pattern
)


tests = [

    [

        {
            "opening":
                "tilt_turn"
        }
    ],

    [

        {
            "opening":
                "tilt_turn"
        },

        {
            "opening":
                "tilt_turn"
        }
    ],

    [

        {
            "opening":
                "fixed"
        },

        {
            "opening":
                "tilt_turn"
        }
    ],

    [

        {
            "opening":
                "tilt_turn"
        },

        {
            "opening":
                "fixed"
        }
    ]
]

for segments in tests:

    pattern = detect_pattern(
        segments
    )

    print(
        pattern
    )