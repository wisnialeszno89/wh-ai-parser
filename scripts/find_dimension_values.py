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

    1000,
    1200,
    1400
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


def scan_ints(data):

    hits = []

    for i in range(
        len(data) - 4
    ):

        value = struct.unpack(
            "<I",
            data[i:i+4]
        )[0]

        if value in TARGETS:

            hits.append(
                (i, value)
            )

    return hits


def main():

    for file_name in FILES:

        print("\n================")
        print(file_name)

        data = load(
            BASE_DIR / file_name
        )

        hits = scan_ints(data)

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