import zlib


BASE = (
    "research/template_matrix/"
    "double_sash_movable_mullion/"
)


FILES = {

    "2100x1300":
        BASE + "2100x1300.ofr",

    "2500x1300":
        BASE + "2500x1300.ofr",

    "2100x1500":
        BASE + "2100x1500.ofr",

    "2500x1500":
        BASE + "2500x1500.ofr",
}


def load_payload(path):

    with open(path, "rb") as f:

        data = f.read()

    offset = data.find(
        b"\x78\xDA"
    )

    stream = data[offset:]

    return zlib.decompress(
        stream
    )


def diff_regions(a, b):

    max_len = min(
        len(a),
        len(b)
    )

    diffs = []

    for i in range(max_len):

        if a[i] != b[i]:

            diffs.append(i)

    clusters = []

    if diffs:

        start = diffs[0]
        prev = diffs[0]

        for d in diffs[1:]:

            if d - prev > 16:

                clusters.append(
                    (start, prev)
                )

                start = d

            prev = d

        clusters.append(
            (start, prev)
        )

    return clusters


payload_2100x1300 = load_payload(
    FILES["2100x1300"]
)

payload_2500x1300 = load_payload(
    FILES["2500x1300"]
)

payload_2100x1500 = load_payload(
    FILES["2100x1500"]
)


width_clusters = diff_regions(

    payload_2100x1300,

    payload_2500x1300
)

height_clusters = diff_regions(

    payload_2100x1300,

    payload_2100x1500
)


print()
print("========== WIDTH CLUSTERS ==========")
print()

for c in width_clusters:

    size = c[1] - c[0]

    print(
        f"{c[0]} - {c[1]}"
        f" (size={size})"
    )


print()
print("========== HEIGHT CLUSTERS ==========")
print()

for c in height_clusters:

    size = c[1] - c[0]

    print(
        f"{c[0]} - {c[1]}"
        f" (size={size})"
    )