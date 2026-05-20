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


print(
    "\n========== DIFF CANDIDATES ==========\n"
)


for i in range(
    0,
    min(len(A), len(B)) - 4
):

    chunk_a = A[i:i+4]
    chunk_b = B[i:i+4]

    if chunk_a != chunk_b:

        try:

            val_a = struct.unpack(
                "<I",
                chunk_a
            )[0]

            val_b = struct.unpack(
                "<I",
                chunk_b
            )[0]

            delta = abs(
                val_a - val_b
            )

            if delta < 10000:

                print(
                    f"{i}: "
                    f"{val_a} -> {val_b}"
                )

        except:

            pass