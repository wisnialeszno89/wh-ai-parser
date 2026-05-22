from pathlib import Path
import zlib


BASE_FILE = Path(
    "research/semantic_dataset/RU 1000x1000.OFR"
)

PATCH_FILE = Path(
    "research/semantic_dataset/RU 1000x1000 3 szyby.OFR"
)

OUTPUT_FILE = Path(
    "generated_offers/generated_full_patch.OFR"
)


def load_raw(path):

    with open(path, "rb") as f:

        return f.read()


def decompress_payload(raw):

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

    return header, decompressed


def find_diff_regions(a, b):

    diffs = []

    for i in range(
        min(len(a), len(b))
    ):

        if a[i] != b[i]:

            diffs.append(i)

    if not diffs:

        return []

    regions = []

    start = diffs[0]
    prev = diffs[0]

    for x in diffs[1:]:

        if x - prev > 8:

            regions.append(
                (start, prev)
            )

            start = x

        prev = x

    regions.append(
        (start, prev)
    )

    return regions


def main():

    base_raw = load_raw(
        BASE_FILE
    )

    patch_raw = load_raw(
        PATCH_FILE
    )

    header, base = decompress_payload(
        base_raw
    )

    _, patch = decompress_payload(
        patch_raw
    )

    regions = find_diff_regions(
        base,
        patch
    )

    print(
        f"\nTOTAL REGIONS: "
        f"{len(regions)}"
    )

    for start, end in regions:

        base[
            start:end+1
        ] = patch[
            start:end+1
        ]

    recompressed = zlib.compress(
        bytes(base)
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