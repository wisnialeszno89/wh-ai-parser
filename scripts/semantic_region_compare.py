from pathlib import Path
import zlib


BASE_FILE = Path(
    "research/semantic_dataset/RU 1000x1000.OFR"
)


TEST_FILES = [

    "RU 1000x1200.OFR",
    "RU 1200x1000.OFR",
    "RU 1400x1000.OFR",
   ]


BASE_DIR = Path(
    "research/semantic_dataset"
)


def load_decompressed(path):

    with open(path, "rb") as f:

        data = f.read()

    start = data.find(
        b"\x78\xda"
    )

    compressed = data[start:]

    return zlib.decompress(
        compressed
    )


def diff_regions(a, b):

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

    base = load_decompressed(
        BASE_FILE
    )

    for file_name in TEST_FILES:

        print("\n========================")
        print(file_name)

        test = load_decompressed(
            BASE_DIR / file_name
        )

        regions = diff_regions(
            base,
            test
        )

        print(
            f"\nTOTAL REGIONS: "
            f"{len(regions)}"
        )

        for start, end in regions[:80]:

            size = (
                end
                - start
                + 1
            )

            print(
                f"{start}-{end} "
                f"size={size}"
            )


if __name__ == "__main__":

    main()