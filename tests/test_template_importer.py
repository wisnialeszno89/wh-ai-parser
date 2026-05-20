from app.services.template_importer import (
    add_template
)


result = add_template(

    construction_id=
    "double_sash_movable_mullion",

    template_path=
    "research/template_matrix/double_sash_movable_mullion/2100x1500.ofr"
)


print()
print(result)