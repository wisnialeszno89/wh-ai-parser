import zlib


INPUT = (
    "research/payloads/fix_ru_fix/"
    "OFR-2044-TT.OFR"
)

OUTPUT = (
    "outputs/ofr/"
    "patched_2400x1500.ofr"
)


with open(INPUT, "rb") as f:

    original = f.read()


# =====================================
# FIND ZLIB
# =====================================

offset = original.find(b"\x78\xDA")

if offset == -1:

    raise Exception("NO ZLIB")


header = original[:offset]

payload = zlib.decompress(
    original[offset:]
)


# =====================================
# PATCH
# =====================================

payload = payload.replace(

    b"2100x1300",

    b"2400x1500"
)


# =====================================
# RECOMPRESS
# =====================================

compressed = zlib.compress(payload)


final = header + compressed


with open(OUTPUT, "wb") as f:

    f.write(final)


print(
    f"[+] SAVED: {OUTPUT}"
)