from pathlib import Path
import zlib


FILE = Path(
    "research/semantic_dataset/ru/RU 1000x1000.OFR"
)


def main():

    with open(FILE, "rb") as f:

        data = f.read()

    start = data.find(
        b"\x78\xda"
    )

    if start == -1:

        print(
            "NO ZLIB HEADER"
        )

        return

    print(
        f"ZLIB START: {start}"
    )

    compressed = data[start:]

    try:

        decompressed = zlib.decompress(
            compressed
        )

        print(
            "\nDECOMPRESSED SIZE:",
            len(decompressed)
        )

        with open(
            "decompressed.bin",
            "wb"
        ) as f:

            f.write(decompressed)

        print(
            "\nSAVED: decompressed.bin"
        )

    except Exception as e:

        print(
            "\nERROR:"
        )

        print(e)


if __name__ == "__main__":

    main()