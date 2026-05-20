import zlib


FILES = {

    "base":

        "research/payloads/"
        "fix_ru_fix/"
        "OFR-2044-TT.OFR",


    "width":

    "research/payloads/"
    "fix_ru_fix/"
    "OFR-2053-.OFR",


    "height":

    "research/payloads/"
    "fix_ru_fix/"
    "OFR-2055-.OFR",


    "both":

    "research/payloads/"
    "fix_ru_fix/"
    "OFR-2056-.OFR"
}


payloads = {}


for name, path in FILES.items():

    with open(path, "rb") as f:

        data = f.read()

    offset = data.find(
        b"\x78\xDA"
    )

    payload = zlib.decompress(
        data[offset:]
    )

    payloads[name] = payload


base = payloads["base"]
width = payloads["width"]
height = payloads["height"]
both = payloads["both"]


print(
    "\n========== WIDTH OFFSETS ==========\n"
)


width_offsets = []


for i in range(
    min(len(base), len(width))
):

    if base[i] != width[i]:

        if (
            base[i] == height[i]
        ):

            width_offsets.append(i)

            print(

                f"{i}: "

                f"{base[i]:02X} -> "

                f"{width[i]:02X}"
            )


print(
    "\nTOTAL WIDTH OFFSETS:",
    len(width_offsets)
)


print(
    "\n========== HEIGHT OFFSETS ==========\n"
)


height_offsets = []


for i in range(
    min(len(base), len(height))
):

    if base[i] != height[i]:

        if (
            base[i] == width[i]
        ):

            height_offsets.append(i)

            print(

                f"{i}: "

                f"{base[i]:02X} -> "

                f"{height[i]:02X}"
            )


print(
    "\nTOTAL HEIGHT OFFSETS:",
    len(height_offsets)
)
print(
    "\n========== WIDTH SAMPLE ==========\n"
)

print(
    width_offsets[:50]
)


print(
    "\n========== HEIGHT SAMPLE ==========\n"
)

print(
    height_offsets[:50]
)