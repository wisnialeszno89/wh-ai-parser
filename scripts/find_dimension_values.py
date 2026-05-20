import zlib
import struct


TARGETS = [

    2100,
    2500,
    1300,
    1500,

    210.0,
    250.0,
    130.0,
    150.0,

    21.0,
    25.0,
    13.0,
    15.0
]


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

    "research/payloads/fix_ru_fix/"
    "OFR-2044-TT.OFR"
)


print()
print("========== FLOAT SEARCH ==========")
print()


for i in range(

    0,

    len(payload) - 4,

    4
):

    chunk = payload[i:i+4]

    try:

        value = struct.unpack(
            "<f",
            chunk
        )[0]

        for target in TARGETS:

            if abs(value - target) < 0.01:

                print(
                    f"FLOAT @ {i}: {value}"
                )

    except:

        pass


print()
print("========== INT SEARCH ==========")
print()


for i in range(

    0,

    len(payload) - 4,

    4
):

    chunk = payload[i:i+4]

    value = struct.unpack(
        "<I",
        chunk
    )[0]

    if value in TARGETS:

        print(
            f"INT @ {i}: {value}"
        )