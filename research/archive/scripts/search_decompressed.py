FILE = "decompressed.bin"


KEYWORDS = [

    "1000",
    "Perfectline",
    "Softline",
    "Ug",
    "4/16/4",
    "antra",
    "eiche",
    "white",
    "RU",
    "CGlass",
    "CSzyba"
]


def main():

    with open(FILE, "rb") as f:

        data = f.read()

    text = data.decode(

        "latin1",
        errors="ignore"
    )

    for key in KEYWORDS:

        idx = text.find(key)

        print("\n================")
        print(f"KEYWORD: {key}")

        if idx == -1:

            print("NOT FOUND")
            continue

        print(
            f"FOUND AT: {idx}"
        )

        start = max(
            0,
            idx - 120
        )

        end = idx + 120

        snippet = text[
            start:end
        ]

        print("\nSNIPPET:\n")

        print(snippet)


if __name__ == "__main__":

    main()