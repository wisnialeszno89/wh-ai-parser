from app.wh.zlib_stream import (
    extract_payload,
    build_ofr
)

from app.wh.payload.patch_dimensions import (
    patch_dimensions
)


INPUT = (
    "research/payloads/fix_ru_fix/"
    "OFR-2044-TT.OFR"
)

OUTPUT = (
    "outputs/ofr/"
    "patched_2400x1500.ofr"
)


with open(INPUT, "rb") as f:

    data = f.read()


header, payload = extract_payload(
    data
)


payload = patch_dimensions(

    payload,

    "2100x1300",

    "2400x1500"
)


rebuilt = build_ofr(
    header,
    payload
)


with open(OUTPUT, "wb") as f:

    f.write(rebuilt)


print(
    "[+] PATCHED OFR SAVED"
)