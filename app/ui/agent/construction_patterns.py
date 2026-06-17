SINGLE_SASH = (
    "single_sash"
)

DOUBLE_SASH = (
    "double_sash"
)

FIX_PLUS_SASH = (
    "fix_plus_sash"
)

SASH_PLUS_FIX = (
    "sash_plus_fix"
)

DOUBLE_FIX = (
    "double_fix"
)


def detect_pattern(
    segments
):

    count = len(
        segments
    )

    if count == 1:

        opening = (
            segments[0].get(
                "opening"
            )
        )

        if opening == "fixed":

            return DOUBLE_FIX

        return SINGLE_SASH

    if count != 2:

        return None

    left = segments[0].get(
        "opening"
    )

    right = segments[1].get(
        "opening"
    )

    if (

        left == "fixed"

        and

        right != "fixed"
    ):

        return FIX_PLUS_SASH

    if (

        left != "fixed"

        and

        right == "fixed"
    ):

        return SASH_PLUS_FIX

    if (

        left == "fixed"

        and

        right == "fixed"
    ):

        return DOUBLE_FIX

    return DOUBLE_SASH