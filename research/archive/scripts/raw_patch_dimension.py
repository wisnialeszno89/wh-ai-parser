INPUT = (
    "research/payloads/fix_ru_fix/"
    "OFR-2044-TT.OFR"
)

OUTPUT = (
    "outputs/ofr/"
    "raw_patched.ofr"
)


OLD = (
    "2100x1300"
    .encode("utf-16-le")
)

NEW = (
    "2400x1500"
    .encode("utf-16-le")
)


with open(INPUT, "rb") as f:

    data = bytearray(
        f.read()
    )


idx = data.find(OLD)

print(
    "\nOFFSET:",
    idx
)


if idx == -1:

    raise Exception(
        "DIMENSIONS NOT FOUND"
    )


if len(OLD) != len(NEW):

    raise Exception(
        "LENGTH MISMATCH"
    )


data[
    idx:idx + len(OLD)
] = NEW


with open(OUTPUT, "wb") as f:

    f.write(data)


print(
    "\n[+] RAW PATCHED"
)