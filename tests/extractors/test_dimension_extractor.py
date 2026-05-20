from app.parsers.extractors.dimension_extractor import (
    extract_dimensions
)


TEST_CASES = [

    "Okno 1550x1435",

    "Wymiar 2090 x 1440",

    "1500/2300",

    "Szerokość 1800 wysokość 1500",

    "HST 3500x2300 antracyt",

    "Drzwi 1100x2100",

    "155Ox1435",

    "209O x 144O",

    "1500*2300",

    "1500-2300",

    "Szerokosc 1800 Wysokosc 1500",
]


for text in TEST_CASES:

    result = extract_dimensions(
        text
    )

    print()

    print(text)

    print(result)