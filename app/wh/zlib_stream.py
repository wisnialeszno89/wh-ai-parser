import zlib


def extract_payload(data: bytes):

    offset = data.find(
        b"\x78\xDA"
    )

    if offset == -1:

        raise Exception(
            "ZLIB HEADER NOT FOUND"
        )

    header = data[:offset]

    payload = zlib.decompress(
        data[offset:]
    )

    return header, payload


def build_ofr(
    header: bytes,
    payload: bytes
):

    compressed = zlib.compress(
    payload,
    level=9
)

    return header + compressed