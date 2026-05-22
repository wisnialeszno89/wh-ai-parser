import re


FILE = (
    "research/dumps/"
    "OFR-2044-TT.bin"
)


with open(FILE, "rb") as f:

    data = f.read()


classes = [

    b"CKwatera",
    b"CSkrzydlo",
    b"CSzyba",
    b"CSlupek",
    b"COsciez",
    b"CPosition"
]


print(
    "\n========== CLASS OFFSETS ==========\n"
)

for cls in classes:

    print(f"\n{cls.decode()}")

    for match in re.finditer(cls, data):

        print(
            f"OFFSET: {match.start()}"
        )