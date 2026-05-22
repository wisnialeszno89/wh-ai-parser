import zlib
import struct


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
print("========== STRUCT VALUES ==========")
print()


for off in TARGET_OFFSETS:

    chunk_a = payload_a[
        off:off+4
    ]

    chunk_b = payload_b[
        off:off+4
    ]

    int_a = struct.unpack(
        "<I",
        chunk_a
    )[0]

    int_b = struct.unpack(
        "<I",
        chunk_b
    )[0]

    try:

        float_a = struct.unpack(
            "<f",
            chunk_a
        )[0]

        float_b = struct.unpack(
            "<f",
            chunk_b
        )[0]

    except:

        float_a = None
        float_b = None


    print()
    print(f"OFFSET {off}")

    print(
        f"INT   : "
        f"{int_a} -> {int_b}"
    )

    print(
        f"FLOAT : "
        f"{float_a} -> {float_b}"
    )