import zlib


BASE = (
    "research/payloads/"
    "fix_ru_fix/"
    "OFR-2044-TT.OFR"
)

WIDTH = (
    "research/payloads/"
    "fix_ru_fix/"
    "OFR-2053-.OFR"
)


def load_payload(path):

    with open(path, "rb") as f:

        data = f.read()

    offset = data.find(
        b"\x78\xDA"
    )

    return bytearray(

        zlib.decompress(
            data[offset:]
        )
    )


base = load_payload(BASE)
width = load_payload(WIDTH)


print(
    "\n========== WIDTH DELTAS ==========\n"
)


for i in range(
    min(len(base), len(width))
):

    if base[i] != width[i]:

        delta = (
            width[i]
            - base[i]
        )

        print(
            f"{i}: "
            f"{base[i]} -> "
            f"{width[i]} "
            f"(delta {delta})"
        )