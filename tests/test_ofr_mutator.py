from app.services.ofr_mutator import (
    mutate_dimensions
)


OUTPUT = mutate_dimensions(

    template_path=
    "app/wh/base_templates/fix_ru.ofr",

    width=2090,

    height=1440,

    output_path=
    "outputs/ofr/generated_fix_ru.ofr"
)


print()
print(OUTPUT)