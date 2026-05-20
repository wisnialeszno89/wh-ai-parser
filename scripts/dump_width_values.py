import zlib


TARGET_OFFSETS = [

    4251,
    4259,
    4268,
    4276,
    4284,
    4292,
    4300,
    4308
]


FILES = {

    "2100x1300":
        "research/template_matrix/"
        "double_sash_movable_mullion/"
        "2100x1300.ofr",

    "2500x1300":
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
    FILES["2100x1300"]
)

payload_b = load_payload(
    FILES["2500x1300"]
)


print()
print("========== WIDTH VALUES ==========")
print()


for off in TARGET_OFFSETS:

    a = payload_a[off]

    b = payload_b[off]

    print(
        f"{off} | "
        f"{a} -> {b}"
    )