import re


FILE = (
    "research/dumps/"
    "OFR-2044-TT.bin"
)


with open(FILE, "rb") as f:

    data = f.read()


matches = re.finditer(

    rb"(?:[\x20-\x7E]\x00){3,}",

    data
)


print(
    "\n========== UTF16 STRINGS ==========\n"
)

for m in matches:

    offset = m.start()

    try:

        text = m.group().decode(
            "utf-16-le"
        )

        print(
            f"{offset}: {text}"
        )

    except:

        pass