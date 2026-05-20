from app.wh.generate_ofr import (
    generate_ofr
)


output = generate_ofr(

    construction_id=(
        "double_sash_movable_mullion"
    ),

    width=2500,

    height=1500,

    output_name="test_generated.ofr"
)

print()

print("========== GENERATED ==========")
print()

print(output)