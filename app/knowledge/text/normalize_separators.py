def normalize_separators(
    text
):

    return (

        text

        .replace(
            "+",
            " "
        )

        .replace(
            "/",
            " "
        )

        .replace(
            "-",
            " "
        )

        .replace(
            "|",
            " "
        )

    )