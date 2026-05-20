from app.parsers.extractors.color_extractor import (
    extract_colors
)


TEST_CASES = [

    "Okno antracyt",

    "Bialy/bialy",

    "Winchester",

    "Orzech",

    "Antracyt / bialy",
]


for text in TEST_CASES:

    result = extract_colors(
        text
    )

    print()
    print(text)

    print(result)