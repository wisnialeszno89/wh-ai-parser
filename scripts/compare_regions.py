FILE_A = (
    "research/hex/CKwatera.bin"
)

FILE_B = (
    "research/hex/CKwatera_2.bin"
)


with open(FILE_A, "rb") as f:
    a = f.read()

with open(FILE_B, "rb") as f:
    b = f.read()


print("\n========== REGION DIFF ==========\n")

for i in range(min(len(a), len(b))):

    if a[i] != b[i]:

        print(
            f"{i:04X}: "
            f"{a[i]:02X} -> "
            f"{b[i]:02X}"
        )