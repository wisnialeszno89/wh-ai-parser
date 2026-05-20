def patch_dimensions(
    payload: bytes,
    old: str,
    new: str
):

    old_b = old.encode(
        "utf-16-le"
    )

    new_b = new.encode(
        "utf-16-le"
    )

    if len(old_b) != len(new_b):

        raise Exception(
            "DIMENSIONS MUST HAVE SAME LENGTH"
        )

    idx = payload.find(old_b)

    if idx == -1:

        raise Exception(
            "OLD DIMENSIONS NOT FOUND"
        )

    payload = bytearray(payload)

    payload[
        idx:idx + len(old_b)
    ] = new_b

    return bytes(payload)