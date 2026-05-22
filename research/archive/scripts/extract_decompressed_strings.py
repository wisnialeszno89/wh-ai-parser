import re


FILE = "decompressed.bin"


def main():

    with open(FILE, "rb") as f:

        data = f.read()

    strings = re.findall(

        rb"[ -~]{4,}",

        data
    )

    decoded = []

    for s in strings:

        try:

            decoded.append(
                s.decode("utf-8")
            )

        except:

            pass

    print(
        "\n========== STRINGS ==========\n"
    )

    for s in decoded:

        print(s)


if __name__ == "__main__":

    main()