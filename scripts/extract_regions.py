import zlib


def load_payload(path):

    with open(path, "rb") as f:

        data = f.read()

    offset = data.find(
        b"\x78\xDA"
    )

    stream = data[offset:]

    return zlib.decompress(
        stream
    )


payload = load_payload(
    "research/payloads/fix_ru_fix/OFR-2044-TT.OFR"
)


START = 3113
END = 4079


region = payload[
    START:END
]


with open(

    "research/dumps/region_3113_4079.bin",

    "wb"

) as f:

    f.write(region)


print()
print("Saved region")
print(
    f"{START} - {END}"
)