from app.wh.mutate_dimensions import (
    mutate_dimensions
)


result = mutate_dimensions(

    "fix_ru_fix",

    2500,

    1500
)


with open(

    "outputs/ofr/"
    "mutation_test.ofr",

    "wb"

) as f:

    f.write(result)


print(
    "\n[+] MUTATION TEST SAVED"
)