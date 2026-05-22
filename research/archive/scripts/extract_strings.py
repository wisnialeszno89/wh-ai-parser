from pathlib import Path
import re


FILE = Path(
    "research/semantic_dataset/ru/RU 1000x1000 SF82.OFR"
)


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

    for s in decoded:

        print(s)


if __name__ == "__main__":

    main()