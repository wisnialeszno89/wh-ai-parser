import re


FILE = "decompressed.bin"


def extract_ascii(data):

    strings = re.findall(

        rb"[ -~]{4,}",

        data
    )

    result = []

    for s in strings:

        try:

            result.append(
                s.decode("utf-8")
            )

        except:

            pass

    return result


def extract_utf16(data):

    result = []

    for i in range(
        0,
        len(data) - 4,
        2
    ):

        chunk = data[
            i:i + 200
        ]

        try:

            text = chunk.decode(
                "utf-16-le",
                errors="ignore"
            )

            cleaned = "".join(

                c for c in text

                if (
                    c.isprintable()
                    or c in "\n\r\t"
                )
            )

            if len(cleaned.strip()) > 8:

                result.append(
                    cleaned.strip()
                )

        except:

            pass

    return result


def main():

    with open(FILE, "rb") as f:

        data = f.read()

    ascii_strings = extract_ascii(
        data
    )

    utf16_strings = extract_utf16(
        data
    )

    with open(
        "strings_dump.txt",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "=== ASCII ===\n\n"
        )

        for s in ascii_strings:

            f.write(s + "\n")

        f.write(
            "\n\n=== UTF16 ===\n\n"
        )

        for s in utf16_strings:

            f.write(s + "\n")

    print(
        "\nSAVED: strings_dump.txt"
    )

    print(
        f"ASCII={len(ascii_strings)}"
    )

    print(
        f"UTF16={len(utf16_strings)}"
    )


if __name__ == "__main__":

    main()