import zlib


FILE = (
    "research/payloads/fix_ru_fix/"
    "OFR-2044-TT.OFR"
)


with open(FILE, "rb") as f:

    data = f.read()


offset = data.find(
    b"\x78\xDA"
)

payload = zlib.decompress(
    data[offset:]
)


needle = (
    "2100x1300"
    .encode("utf-16-le")
)


idx = payload.find(needle)

print(
    "\nDIMENSION OFFSET:",
    idx
)