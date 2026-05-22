from pathlib import Path


FILE_A = (
    "research/payloads/fix_ru_fix/"
    "OFR-2044-TT.OFR"
)

FILE_B = (
    "research/payloads/fix_ru_fix/"
    "OFR-2045-TT.OFR"
)


with open(FILE_A, "rb") as f:
    a = f.read()

with open(FILE_B, "rb") as f:
    b = f.read()


print("\n========== FILE INFO ==========\n")

print("A SIZE:", len(a))
print("B SIZE:", len(b))


print("\n========== DIFF ==========\n")

diffs = []

max_len = min(len(a), len(b))

for i in range(max_len):

    if a[i] != b[i]:

        diffs.append(i)

        print(
            f"OFFSET {i}: "
            f"{a[i]:02X} -> {b[i]:02X}"
        )

print("\n========== SUMMARY ==========\n")

print("TOTAL DIFFS:", len(diffs))


# =====================================
# CLUSTERS
# =====================================

clusters = []

if diffs:

    cluster = [diffs[0]]

    for i in range(1, len(diffs)):

        current = diffs[i]
        prev = diffs[i - 1]

        if current - prev <= 8:

            cluster.append(current)

        else:

            clusters.append(cluster)

            cluster = [current]

    clusters.append(cluster)

print("\n========== CLUSTERS ==========\n")

for c in clusters:

    print(
        f"{c[0]} -> {c[-1]} "
        f"(len={len(c)})"
    )