from pathlib import Path


FILE = (
    "research/payloads/fix_ru_fix/"
    "OFR-2044-TT.OFR"
)


with open(FILE, "rb") as f:

    data = f.read()


print("\n========== FILE INFO ==========\n")

print("SIZE:", len(data))


print("\n========== HEX DUMP ==========\n")

for i in range(0, min(len(data), 512), 16):

    chunk = data[i:i+16]

    hex_values = " ".join(
        f"{b:02X}" for b in chunk
    )

    ascii_values = "".join(

        chr(b)

        if 32 <= b <= 126

        else "."

        for b in chunk
    )

    print(
        f"{i:08X}  "
        f"{hex_values:<48} "
        f"{ascii_values}"
    )