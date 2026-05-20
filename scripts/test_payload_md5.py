import hashlib
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

payload = zlib.decompress(
    stream
)


def md5(data):

    result = hashlib.md5(
        data
    ).hexdigest()

    return "-".join(

        result[i:i+2].upper()

        for i in range(
            0,
            len(result),
            2
        )
    )


print(
    "\n========== FULL FILE ==========\n"
)

print(md5(data))


print(
    "\n========== ZLIB STREAM ==========\n"
)

print(md5(stream))


print(
    "\n========== PAYLOAD ==========\n"
)

print(md5(payload))