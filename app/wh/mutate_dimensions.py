from app.wh.runtime_engine import (
    load_ofr
)


def patch_utf16_text(

    payload,

    offset,

    text
):

    encoded = text.encode(
        "utf-16-le"
    )

    payload[
        offset:
        offset + len(encoded)
    ] = encoded

    return payload


def mutate_dimensions(

    template_path,

    width,

    height,

    text_offset
):

    runtime = load_ofr(
        template_path
    )

    payload = runtime[
        "payload"
    ]

    header = runtime[
        "header"
    ]

    dimension_text = (
        f"{width}x{height}"
    )

    payload = patch_utf16_text(

        payload,

        text_offset,

        dimension_text
    )

    return {

        "header": header,

        "payload": payload
    }