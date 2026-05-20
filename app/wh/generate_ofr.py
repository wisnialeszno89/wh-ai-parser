from pathlib import Path

from app.wh.template_resolver import (
    resolve_template
)

from app.wh.mutate_dimensions import (
    mutate_dimensions
)

from app.wh.runtime_engine import (
    save_ofr
)


TEXT_DIMENSION_OFFSET = 40432


def generate_ofr(

    construction_id,

    width,

    height,

    output_name="generated.ofr"
):

    template_path = resolve_template(
        construction_id
    )

    runtime = mutate_dimensions(

        template_path=template_path,

        width=width,

        height=height,

        text_offset=TEXT_DIMENSION_OFFSET
    )

    output_dir = Path(
        "outputs/ofr"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        output_dir / output_name
    )

    save_ofr(

        header=runtime["header"],

        payload=runtime["payload"],

        output_path=output_path
    )

    return output_path