from pathlib import Path
import zlib


BASE_FILE = Path(
    "research/semantic_dataset/RU 1000x1000.OFR"
)

OUTPUT_FILE = Path(
    "generated_offers/generated_3glass.OFR"
)


PATCHES = [

    (
        27959,
        bytes.fromhex(
            "60 2C F9 85"
        )
    )
]


def main():

    with open(BASE_FILE, "rb") as f:

        raw = f.read()

    start = raw.find(
        b"\x78\xda"
    )

    header = raw[:start]

    compressed = raw[start:]

    decompressed = bytearray(
        zlib.decompress(
            compressed
        )
    )

    for offset, patch in PATCHES:

        decompressed[
            offset:
            offset + len(patch)
        ] = patch

    recompressed = zlib.compress(
        bytes(decompressed)
    )

    rebuilt = (
        header
        + recompressed
    )

    OUTPUT_FILE.parent.mkdir(
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "wb"
    ) as f:

        f.write(rebuilt)

    print(
        "\nSAVED:",
        OUTPUT_FILE
    )


if __name__ == "__main__":

    main()