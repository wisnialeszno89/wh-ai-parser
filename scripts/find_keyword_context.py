FILE = "research/archive/dumps/decompressed.bin"


KEYWORDS = [

    "4/16",
    "Ug",
    "SF82",
    "Softline",
    "Perfectline",
    "antra",
    "eiche",
    "1000",
    "1200"
]


def main():

    with open(FILE, "rb") as f:

        data = f.read()

    text = data.decode(

        "latin1",
        errors="ignore"
    )

    for key in KEYWORDS:

        print("\n================")
        print(f"KEYWORD: {key}")

        found = False

        idx = 0

        while True:

            idx = text.find(
                key,
                idx
            )

            if idx == -1:
                break

            found = True

            print(
                f"\nFOUND AT: {idx}"
            )

            start = max(
                0,
                idx - 200
            )

            end = idx + 200

            snippet = text[
                start:end
            ]

            print(
                "\nSNIPPET:\n"
            )

            print(snippet)

            idx += len(key)

        if not found:

            print("NOT FOUND")


if __name__ == "__main__":

    main()