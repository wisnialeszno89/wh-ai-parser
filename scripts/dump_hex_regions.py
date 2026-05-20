import zlib


START = 4240
END = 4320


FILE = (
    "research/template_matrix/"
    "double_sash_movable_mullion/"
    "2100x1300.ofr"
)


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


payload = load_payload(FILE)

region = payload[
    START:END
]


print()
print("========== HEX REGION ==========")
print()


for i in range(

    0,

    len(region),

    16
):

    chunk = region[i:i+16]

    hex_values = " ".join(

        f"{b:02X}"

        for b in chunk
    )

    print(
        f"{START+i:05d} | "
        f"{hex_values}"
    )