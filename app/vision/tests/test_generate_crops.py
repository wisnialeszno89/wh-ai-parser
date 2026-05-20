from app.vision.preprocessing.generate_crops import (
    generate_crops
)

results = generate_crops(
    "samples/zapytanie1.jpg"
)

for r in results:
    print(r)