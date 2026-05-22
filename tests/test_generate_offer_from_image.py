from app.services.generate_offer_from_image import (
    generate_offer_from_image
)

result = generate_offer_from_image(
    "training_data/multi_layout/page_1.png"
)

print("\nGENERATED:\n")

for r in result:

    print(r)