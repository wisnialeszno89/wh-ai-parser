import zlib


FILE = (
    "research/payloads/"
    "fix_ru_fix/"
    "OFR-2044-TT.OFR"
)


MARKERS = [

    b"CKwatera",

    b"CSkrzydlo",

    b"CSzyba",

    b"COsciez",

    b"CSlupek",

    b"CPosition"
]


with open(FILE, "rb") as f:

    data = f.read()


offset = data.find(
    b"\x78\xDA"
)

payload = zlib.decompress(
    data[offset:]
)


print(
    "\n========== OBJECTS ==========\n"
)


for marker in MARKERS:

    pos = 0

    while True:

        idx = payload.find(
            marker,
            pos
        )

        if idx == -1:

            break

        print(

            f"{marker.decode()} "

            f"@ {idx}"
        )

        pos = idx + 1