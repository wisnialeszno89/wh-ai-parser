import zlib


def load_ofr(path):

    with open(path, "rb") as f:

        data = f.read()

    offset = data.find(
        b"\x78\xDA"
    )

    if offset == -1:

        raise Exception(
            "Missing zlib stream"
        )

    header = data[:offset]

    stream = data[offset:]

    payload = zlib.decompress(
        stream
    )

    return {

        "header": header,

        "payload": bytearray(
            payload
        )
    }


def save_ofr(

    header,

    payload,

    output_path
):

    compressed = zlib.compress(
        bytes(payload),
        level=9
    )

    with open(output_path, "wb") as f:

        f.write(
            header + compressed
        )