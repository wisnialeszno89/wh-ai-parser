import zlib


WIDTH_REGION = (
    3144,
    3545
)

HEIGHT_REGION = (
    1746,
    2006
)


def extract_payload(path):

    with open(path, "rb") as f:

        data = f.read()

    offset = data.find(
        b"\x78\xDA"
    )

    header = data[:offset]

    payload = zlib.decompress(
        data[offset:]
    )

    return (
        header,
        bytearray(payload)
    )


def build_ofr(
    header,
    payload
):

    compressed = zlib.compress(
        bytes(payload),
        level=9
    )

    return (
        header +
        compressed
    )


def patch_region(

    target,

    source,

    region
):

    start, end = region

    target[start:end] = (
        source[start:end]
    )


def patch_geometry(

    base_path,

    width_path,

    height_path
):

    header, base = (
        extract_payload(base_path)
    )

    _, width_payload = (
        extract_payload(width_path)
    )

    _, height_payload = (
        extract_payload(height_path)
    )


    patch_region(

        base,

        width_payload,

        WIDTH_REGION
    )


    patch_region(

        base,

        height_payload,

        HEIGHT_REGION
    )


    return build_ofr(
        header,
        base
    )