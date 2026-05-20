ORIGINAL = (
    "research/payloads/fix_ru_fix/"
    "OFR-2044-TT.OFR"
)

REBUILT = (
    "outputs/ofr/"
    "rebuilt.ofr"
)


with open(ORIGINAL, "rb") as f:

    a = f.read()

with open(REBUILT, "rb") as f:

    b = f.read()


print("\n========== FILE SIZES ==========\n")

print("ORIGINAL:", len(a))
print("REBUILT :", len(b))


print("\n========== DIFF ==========\n")

count = 0

for i in range(min(len(a), len(b))):

    if a[i] != b[i]:

        print(
            f"{i}: "
            f"{a[i]:02X} -> "
            f"{b[i]:02X}"
        )

        count += 1

        if count > 50:

            break


print("\nTOTAL DIFFS:", count)