import zlib


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


CENTER = 40432
RANGE = 256


start = CENTER - RANGE
end = CENTER + RANGE


print(
    "\n========== REGION DIFF ==========\n"
)


for i in range(start, end):

    if A[i] != B[i]:

        print(

            f"{i}: "

            f"{A[i]:02X} -> "

            f"{B[i]:02X}"
        )