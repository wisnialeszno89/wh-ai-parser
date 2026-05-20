from pathlib import Path


BASE_TEMPLATE_DIR = Path(
    "app/wh/base_templates"
)


def resolve_template(
    construction_id: str
):

    template_path = (

        BASE_TEMPLATE_DIR
        /
        f"{construction_id}.ofr"
    )

    if not template_path.exists():

        raise FileNotFoundError(

            f"Missing OFR template: "
            f"{template_path}"
        )

    return template_path