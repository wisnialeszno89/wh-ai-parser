import re


FILE = (
    "research/xls/"
    "OFR-2044-.xls"
)


with open(FILE, "rb") as f:

    data = f.read()


ascii_strings = re.findall(

    rb"[ -~]{4,}",

    data
)


print(
    "\n========== ASCII STRINGS ==========\n"
)


for s in ascii_strings:

    try:

        text = s.decode(
            "latin1"
        )

        print(text)

    except:

        pass