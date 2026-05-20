FILE_A = (
    "research/dumps/"
    "OFR-2044-TT.bin"
)

FILE_B = (
    "research/dumps/"
    "OFR-2045-TT.bin"
)


with open(FILE_A, "rb") as f:

    a = f.read()

with open(FILE_B, "rb") as f:

    b = f.read()


print("\n========== PAYLOAD DIFF ==========\n")

diffs = []

for i in range(min(len(a), len(b))):

    if a[i] != b[i]:

        diffs.append(i)

        print(
            f"{i}: "
            f"{a[i]:02X} -> "
            f"{b[i]:02X}"
        )


print("\nTOTAL:", len(diffs))