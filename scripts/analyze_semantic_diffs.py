from pathlib import Path


BASE_DIR = Path(
    "research/semantic_dataset/ru"
)


def load_bytes(path):

    with open(path, "rb") as f:

        return f.read()


def diff_regions(a, b):

    regions = []

    start = None

    for i in range(
        min(len(a), len(b))
    ):

        if a[i] != b[i]:

            if start is None:
                start = i

        else:

            if start is not None:

                regions.append(
                    (start, i - 1)
                )

                start = None

    if start is not None:

        regions.append(
            (start, len(a) - 1)
        )

    return regions


def main():

    files = sorted(
        BASE_DIR.glob("*.OFR")
    )

    if not files:

        print("NO FILES")
        return

    base = None

    for f in files:

        if (
    "perfectline_2glass_white_1000x1000"
    in f.name.lower()
):

            base = f
            break

    if base is None:

        print("NO BASE FILE")
        return

    base_data = load_bytes(
        base
    )

    print(
        f"\nBASE: {base.name}"
    )

    for f in files:

        if f == base:
            continue

        data = load_bytes(f)

        regions = diff_regions(
            base_data,
            data
        )

        print("\n================")
        print(f.name)

        print(
            f"REGIONS: {len(regions)}"
        )

        total = 0

        for s, e in regions:

            size = e - s + 1

            total += size

            print(
                f"{s}-{e} "
                f"(size={size})"
            )

        print(
            f"TOTAL_CHANGED={total}"
        )


if __name__ == "__main__":

    main()