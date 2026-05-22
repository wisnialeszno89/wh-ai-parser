import zlib
from pathlib import Path


FILES = [

    (
        "research/payloads/fix_ru_fix/"
        "OFR-2044-TT.OFR"
    ),

    (
        "research/payloads/fix_ru_fix/"
        "OFR-2045-TT.OFR"
    )
]


for file in FILES:

    with open(file, "rb") as f:

        data = f.read()

    offset = data.find(b"\x78\xDA")

    if offset == -1:

        print(
            f"NO ZLIB: {file}"
        )

        continue

    payload = zlib.decompress(
        data[offset:]
    )

    output = (

        "research/dumps/"
        + Path(file).stem
        + ".bin"
    )

    with open(output, "wb") as f:

        f.write(payload)

    print(
        f"[+] SAVED: {output}"
    )