import zlib


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


def compare_payloads(

    file_a,

    file_b
):

    payload_a = load_payload(
        file_a
    )

    payload_b = load_payload(
        file_b
    )

    max_len = min(
        len(payload_a),
        len(payload_b)
    )

    diffs = []

    for i in range(max_len):

        if payload_a[i] != payload_b[i]:

            diffs.append(i)

    print()
    print("========== DIFF STATS ==========")
    print()

    print(
        f"Total diffs: {len(diffs)}"
    )

    if diffs:

        print()

        print(
            f"First diff: {diffs[0]}"
        )

        print(
            f"Last diff: {diffs[-1]}"
        )

    print()
    print("========== DIFF CLUSTERS ==========")
    print()

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

    for c in clusters:

        size = c[1] - c[0]

        print(
            f"{c[0]} - {c[1]}"
            f" (size={size})"
        )


compare_payloads(

    "research/payloads/fix_ru_fix/OFR-2044-TT.OFR",

    "research/payloads/fix_ru_fix/OFR-2053-.OFR"
)