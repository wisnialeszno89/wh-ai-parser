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

    return zlib.decompress(
        data[offset:]
    )


payload = load_payload(FILE)


region = payload[
    START:END
]


print()
print("========== 8 BYTE RECORDS ==========")
print()


for i in range(

    0,

    len(region),

    8
):

    chunk = region[i:i+8]

    hex_values = " ".join(

        f"{b:02X}"

        for b in chunk
    )

    print(
        f"{START+i:05d} | "
        f"{hex_values}"
    )