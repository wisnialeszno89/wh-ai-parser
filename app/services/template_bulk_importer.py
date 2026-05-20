from pathlib import Path

from app.services.template_importer import (
    add_template
)


def bulk_import_templates(

    construction_id: str,

    directory: str
):

    directory_path = Path(
        directory
    )


    imported = []


    for file in directory_path.rglob(
        "*.ofr"
    ):

        result = add_template(

            construction_id=
            construction_id,

            template_path=
            str(file)
        )

        imported.append(
            result
        )


    return imported