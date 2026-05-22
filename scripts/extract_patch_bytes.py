from pathlib import Path
import zlib


BASE_FILE = Path(
    "research/semantic_dataset/RU 1000x1000.OFR"
)

PATCH_FILE = Path(
    "research/semantic_dataset/RU 1000x1000 antra_ws.OFR"
)

PATCH_REGIONS = [

    (5556, 5556),
    (5859, 5859),
    (6153, 6153),
    (21344, 21344),
    (27959, 27962),
    (29336, 29342),
    (29680, 29685)
]


PATCH_REGIONS = [

    (27959, 27962)
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


def to_hex(data):

    return " ".join(
        f"{x:02X}"
        for x in data
    )


def main():

    base = load(
        BASE_FILE
    )

    patched = load(
        PATCH_FILE
    )

    print("\n========== PATCHES ==========\n")

    for start, end in PATCH_REGIONS:

        a = base[
            start:end+1
        ]

        b = patched[
            start:end+1
        ]

        print(
            f"REGION {start}-{end}"
        )

        print(
            "\nBASE:"
        )

        print(
            to_hex(a)
        )

        print(
            "\nPATCH:"
        )

        print(
            to_hex(b)
        )

        print("\n---\n")


if __name__ == "__main__":

    main()