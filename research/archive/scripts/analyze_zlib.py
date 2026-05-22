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

stream = data[offset:]


print(
    "\n========== ZLIB INFO ==========\n"
)

print(
    "OFFSET:",
    offset
)

print(
    "HEADER:",
    stream[:2].hex()
)

print(
    "ADLER32:",
    stream[-4:].hex()
)

payload = zlib.decompress(
    stream
)

print(
    "PAYLOAD SIZE:",
    len(payload)
)

print(
    "COMPRESSED SIZE:",
    len(stream)
)