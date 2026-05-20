from app.parsers.extractors.category_extractor import (
    extract_category
)


TEST_CASES = [

    "Okno 1500x1500",

    "HST 3500x2300",

    "PSK 2500x2300",

    "Drzwi 1100x2100",

    "Brama garazowa 5000x2250",

    "Roleta elektryczna",
]


for text in TEST_CASES:

    result = extract_category(
        text
    )

    print()
    print(text)

    print(result)