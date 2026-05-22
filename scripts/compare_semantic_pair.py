from pathlib import Path
import zlib


FILE_A = Path(
    "research/semantic_dataset/ru/RU 1000x1000.OFR"
)

FILE_B = Path(
    "research/semantic_dataset/ru/RU 1000x1000 SF82.OFR"
)


def load_and_decompress(path):

    with open(path, "rb") as f:

        data = f.read()

    start = data.find(
        b"\x78\xda"
    )

    compressed = data[start:]

    decompressed = zlib.decompress(
        compressed
    )

    return decompressed


def main():

    a = load_and_decompress(
        FILE_A
    )

    b = load_and_decompress(
        FILE_B
    )

    diffs = []

    for i in range(
        min(len(a), len(b))
    ):

        if a[i] != b[i]:

            diffs.append(i)

    print(
        "\nTOTAL DIFFS:",
        len(diffs)
    )

    if not diffs:

        print(
            "\nNO DIFFS"
        )

        return

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

    print("\nREGIONS:\n")

    for region_start, region_end in regions:

        size = (
            region_end
            - region_start
            + 1
        )

        print(
            f"{region_start}-{region_end} "
            f"size={size}"
        )


if __name__ == "__main__":

    main()