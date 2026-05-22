import shutil
from pathlib import Path

from app.vision_llm.multi_layout_parser import (
    parse_multi_layout
)

from app.services.build_template_key import (
    build_template_key
)

from app.services.resolve_template import (
    resolve_template
)


OUTPUT_DIR = Path(
    "generated_offers"
)

OUTPUT_DIR.mkdir(
    exist_ok=True
)


def generate_offer_from_image(
    image_path: str
):

    constructions = parse_multi_layout(
        image_path
    )

    generated = []

    for i, construction in enumerate(
        constructions
    ):

        template_key = (
            build_template_key(
                construction
            )
        )

        template_path = (
            resolve_template(
                template_key
            )
        )

        if template_path is None:

            print(
                f"NO TEMPLATE: "
                f"{template_key}"
            )

            continue

        output_path = (
            OUTPUT_DIR /
            f"generated_{i}.OFR"
        )

        shutil.copy(
            template_path,
            output_path
        )

        generated.append({

            "template_key": template_key,

            "output_path": str(
                output_path
            ),

            "construction": construction
        })

    return generated