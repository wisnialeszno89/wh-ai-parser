from app.services.template_bulk_importer import (
    bulk_import_templates
)


results = bulk_import_templates(

    construction_id=
    "double_sash_movable_mullion",

    directory=
    "research/template_matrix/double_sash_movable_mullion"
)


print()

for item in results:

    print(item)