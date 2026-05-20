import re


def split_offer_blocks(
    text: str
):

    text = text.strip()


    raw_blocks = re.split(

        r"\n\s*\n",

        text
    )

    blocks = []


    for block in raw_blocks:

        cleaned = block.strip()

        if cleaned:

            blocks.append(
                cleaned
            )


    return blocks