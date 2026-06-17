PATTERN_REGISTRY = {

    "single_sash": {

        "operations": [

            "create_sash"
        ]
    },

    "double_sash": {

        "operations": [

            "insert_vertical",

            "create_left_sash",

            "create_right_sash"
        ]
    },

    "fix_plus_sash": {

        "operations": [

            "insert_vertical",

            "create_left_fix",

            "create_right_sash"
        ]
    },

    "sash_plus_fix": {

        "operations": [

            "insert_vertical",

            "create_left_sash",

            "create_right_fix"
        ]
    },

    "double_fix": {

        "operations": [

            "insert_vertical",

            "create_left_fix",

            "create_right_fix"
        ]
    }
}


def get_pattern_definition(
    pattern_name: str
):

    return PATTERN_REGISTRY.get(
        pattern_name
    )