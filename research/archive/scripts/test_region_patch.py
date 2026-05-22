import zlib
from pathlib import Path


SOURCE = (
    "research/template_matrix/"
    "double_sash_movable_mullion/"
    "2100x1300.ofr"
)

DONOR = (
    "research/template_matrix/"
    "double_sash_movable_mullion/"
    "2500x1300.ofr"
)


OUTPUT = (
    "outputs/ofr/"
    "region_patch_test.ofr"
)

PATCHES = [

    (4251, 200),

    (4259, 200),

    (4268, 152),

    (4276, 152)
]


def split_ofr(path):

    with open(path, "rb") as f:

        data = f.read()

    offset = data.find(
        b"\x78\xDA"
    )

    header = data[:offset]

    payload = zlib.decompress(
        data[offset:]
    )

    return header, bytearray(payload)


source_header, source_payload = (
    split_ofr(SOURCE)
)

_, donor_payload = split_ofr(
    DONOR
)


for offset, value in PATCHES:

    source_payload[
        offset
    ] = value


compressed = zlib.compress(
    bytes(source_payload),
    level=9
)


Path(
    "outputs/ofr"
).mkdir(

    parents=True,
    exist_ok=True
)


with open(OUTPUT, "wb") as f:

    f.write(
        source_header +
        compressed
    )


print()
print("Saved:")
print(OUTPUT)