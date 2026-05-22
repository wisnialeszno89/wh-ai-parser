from pathlib import Path
import zlib
import struct


FILES = [

    "RU 1000x1000.OFR",
    "RU 1200x1000.OFR",
    "RU 1400x1000.OFR",
    "RU 1000x1200.OFR"
]


BASE_DIR = Path(
    "research/semantic_dataset"
)


TARGETS = [

    1000.0,
    1200.0,
    1400.0
]


def load(path):

    with open(path, "rb") as f:

        data = f.read()

    start = data.find(
        b"\x78\xda"
    )

    return zlib.decompress(
        data[start:]
    )


def scan_floats(data):

    hits = []

    for i in range(
        len(data) - 4
    ):

        value = struct.unpack(
            "<f",
            data[i:i+4]
        )[0]

        rounded = round(
            value,
            2
        )

        if rounded in TARGETS:

            hits.append(
                (i, rounded)
            )

    return hits


def main():

    for file_name in FILES:

        print("\n================")
        print(file_name)

        data = load(
            BASE_DIR / file_name
        )

        hits = scan_floats(data)

        print(
            f"\nTOTAL HITS: "
            f"{len(hits)}"
        )

        for pos, value in hits[:100]:

            print(
                f"{pos} -> {value}"
            )


if __name__ == "__main__":

    main()