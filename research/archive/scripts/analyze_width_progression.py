from pathlib import Path


FILES = [

    "RU 1000x1000.OFR",
    "RU 1200x1000.OFR",
    "RU 1400x1000.OFR",
    "RU 1600x1000.OFR"
]


BASE_DIR = Path(
    "research/semantic_dataset/ru"
)


def load(path):

    with open(path, "rb") as f:

        return f.read()


def compare(a, b):

    diffs = []

    for i in range(
        min(len(a), len(b))
    ):

        if a[i] != b[i]:

            delta = (
                b[i] - a[i]
            )

            diffs.append(
                (i, delta)
            )

    return diffs


def main():

    datasets = []

    for f in FILES:

        path = BASE_DIR / f

        data = load(path)

        datasets.append(
            (f, data)
        )

    for i in range(
        len(datasets) - 1
    ):

        name_a, a = datasets[i]

        name_b, b = datasets[i + 1]

        diffs = compare(a, b)

        print("\n====================")
        print(
            f"{name_a}"
        )

        print("→")

        print(
            f"{name_b}"
        )

        print(
            f"DIFFS={len(diffs)}"
        )

        for offset, delta in diffs[:100]:

            print(
                f"{offset} "
                f"delta={delta}"
            )


if __name__ == "__main__":

    main()