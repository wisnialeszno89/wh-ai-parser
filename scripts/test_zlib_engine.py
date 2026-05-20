from app.wh.zlib_stream import (
    extract_payload,
    build_ofr
)


INPUT = (
    "research/payloads/fix_ru_fix/"
    "OFR-2044-TT.OFR"
)

OUTPUT = (
    "outputs/ofr/"
    "rebuilt.ofr"
)


with open(INPUT, "rb") as f:

    data = f.read()


header, payload = extract_payload(
    data
)


rebuilt = build_ofr(
    header,
    payload
)


with open(OUTPUT, "wb") as f:

    f.write(rebuilt)


print(
    "[+] REBUILT OFR SAVED"
)