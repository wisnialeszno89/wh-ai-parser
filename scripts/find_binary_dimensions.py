import zlib
import struct


FILES = [

    (
        "A",
        "research/payloads/fix_ru_fix/"
        "OFR-2044-TT.OFR"
    ),

    (
        "B",
        "research/payloads/fix_ru_fix/"
        "OFR-2045-TT.OFR"
    )
]


payloads = {}


for name, path in FILES:

    with open(path, "rb") as f:

        data = f.read()

    offset = data.find(
        b"\x78\xDA"
    )

    payload = zlib.decompress(
        data[offset:]
    )

    payloads[name] = payload


A = payloads["A"]
B = payloads["B"]


TARGETS = [

    (2100, 2500),

    (1300, 1500)
]


print(
    "\n========== DIMENSION MATCHES ==========\n"
)


for i in range(
    0,
    min(len(A), len(B)) - 4
):

    a4 = A[i:i+4]
    b4 = B[i:i+4]

    try:

        va = struct.unpack(
            "<I",
            a4
        )[0]

        vb = struct.unpack(
            "<I",
            b4
        )[0]

        for ta, tb in TARGETS:

            if va == ta and vb == tb:

                print(
                    f"INT32 @ {i}: "
                    f"{va} -> {vb}"
                )

    except:

        pass


for i in range(
    0,
    min(len(A), len(B)) - 2
):

    a2 = A[i:i+2]
    b2 = B[i:i+2]

    try:

        va = struct.unpack(
            "<H",
            a2
        )[0]

        vb = struct.unpack(
            "<H",
            b2
        )[0]

        for ta, tb in TARGETS:

            if va == ta and vb == tb:

                print(
                    f"INT16 @ {i}: "
                    f"{va} -> {vb}"
                )

    except:

        pass