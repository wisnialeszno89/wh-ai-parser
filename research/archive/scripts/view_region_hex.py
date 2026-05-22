FILE = (
    "research/hex/CKwatera.bin"
)


with open(FILE, "rb") as f:

    data = f.read()


for i in range(0, len(data), 16):

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