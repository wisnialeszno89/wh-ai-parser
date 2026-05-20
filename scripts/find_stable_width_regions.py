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


def get_diff_offsets(a, b):

    max_len = min(
        len(a),
        len(b)
    )

    diffs = set()

    for i in range(max_len):

        if a[i] != b[i]:

            diffs.add(i)

    return diffs


payload_2100x1300 = load_payload(
    FILES["2100x1300"]
)

payload_2500x1300 = load_payload(
    FILES["2500x1300"]
)

payload_2100x1500 = load_payload(
    FILES["2100x1500"]
)

payload_2500x1500 = load_payload(
    FILES["2500x1500"]
)


width_diff_a = get_diff_offsets(

    payload_2100x1300,

    payload_2500x1300
)

width_diff_b = get_diff_offsets(

    payload_2100x1500,

    payload_2500x1500
)


common = sorted(
    width_diff_a.intersection(
        width_diff_b
    )
)


print()
print("========== COMMON WIDTH OFFSETS ==========")
print()

print(
    f"Total common offsets: "
    f"{len(common)}"
)

print()

for i in common[:500]:

    print(i)