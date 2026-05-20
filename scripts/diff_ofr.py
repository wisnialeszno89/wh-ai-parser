from pathlib import Path


FILE_A = "templates/base/fix_ru_fix_2100x1300.ofr"
FILE_B = "templates/base/fix_ru_fix_2500x1500.ofr"


with open(FILE_A, "rb") as f:
    a = f.read()

with open(FILE_B, "rb") as f:
    b = f.read()


print("\n========== DIFF ==========\n")

max_len = min(len(a), len(b))

for i in range(max_len):

    if a[i] != b[i]:

        print(
            f"OFFSET {i}: "
            f"{a[i]:02X} -> {b[i]:02X}"
        )