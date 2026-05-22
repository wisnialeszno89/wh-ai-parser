from pathlib import Path


FILE = Path(
    "research/semantic_dataset/ru/RU 1000x1000.OFR"
)


def main():

    with open(FILE, "rb") as f:

        data = f.read(256)

    print("\nHEX:\n")

    print(
        data.hex(" ")
    )

    print("\nASCII:\n")

    ascii_view = ""

    for b in data:

        if 32 <= b <= 126:

            ascii_view += chr(b)

        else:

            ascii_view += "."

    print(ascii_view)


if __name__ == "__main__":

    main()