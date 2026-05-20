import zlib


START = 4240
END = 4320


FILES = {

    "2100":
        "research/template_matrix/"
        "double_sash_movable_mullion/"
        "2100x1300.ofr",

    "2500":
        "research/template_matrix/"
        "double_sash_movable_mullion/"
        "2500x1300.ofr"
}


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


payload_a = load_payload(
    FILES["2100"]
)

payload_b = load_payload(
    FILES["2500"]
)


region_a = payload_a[
    START:END
]

region_b = payload_b[
    START:END
]


print()
print("========== REGION COMPARE ==========")
print()


for i in range(

    0,

    len(region_a),

    16
):

    chunk_a = region_a[i:i+16]
    chunk_b = region_b[i:i+16]

    hex_a = " ".join(
        f"{b:02X}"
        for b in chunk_a
    )

    hex_b = " ".join(
        f"{b:02X}"
        for b in chunk_b
    )

    print(
        f"{START+i:05d}"
    )

    print(
        f"A: {hex_a}"
    )

    print(
        f"B: {hex_b}"
    )

    print()