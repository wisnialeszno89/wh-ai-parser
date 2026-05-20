import hashlib


def calculate_md5(
    data: bytes
):

    md5 = hashlib.md5(
        data
    ).hexdigest()

    return "-".join(

        md5[i:i+2].upper()

        for i in range(
            0,
            len(md5),
            2
        )
    )