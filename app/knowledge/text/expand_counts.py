import re


def expand_counts(
    text
):

    tokens = text.split()

    expanded_tokens = []

    i = 0

    while i < len(
        tokens
    ):

        token = tokens[
            i
        ]

        #
        # 2X DK
        #

        count_match = re.fullmatch(

            r"(\d+)X",

            token

        )

        if (

            count_match

            and

            i + 1 < len(
                tokens
            )

        ):

            count = int(

                count_match.group(
                    1
                )

            )

            expanded_tokens.extend(

                [

                    tokens[
                        i + 1
                    ]

                ]

                * count

            )

            i += 2

            continue

        #
        # 2XDK
        #

        compact_match = re.fullmatch(

            r"(\d+)X([A-Z]+)",

            token

        )

        if compact_match:

            count = int(

                compact_match.group(
                    1
                )

            )

            opening = compact_match.group(
                2
            )

            expanded_tokens.extend(

                [

                    opening

                ]

                * count

            )

            i += 1

            continue

        expanded_tokens.append(
            token
        )

        i += 1

    return " ".join(
        expanded_tokens
    )