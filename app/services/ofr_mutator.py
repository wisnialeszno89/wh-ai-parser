from pathlib import Path


WIDTH_OFFSETS = [

    4251,
    4259,
]


HEIGHT_OFFSETS = [

    4300,
    4308,
]


def patch_int32_le(
    data: bytearray,
    offset: int,
    value: int
):

    data[
        offset:offset+4
    ] = value.to_bytes(
        4,
        "little"
    )


def mutate_dimensions(
    template_path: str,
    width: int,
    height: int,
    output_path: str
):

    with open(
        template_path,
        "rb"
    ) as f:

        data = bytearray(
            f.read()
        )


    for offset in WIDTH_OFFSETS:

        patch_int32_le(
            data,
            offset,
            width
        )


    for offset in HEIGHT_OFFSETS:

        patch_int32_le(
            data,
            offset,
            height
        )


    output = Path(
        output_path
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    with open(
        output,
        "wb"
    ) as f:

        f.write(data)


    return str(output)