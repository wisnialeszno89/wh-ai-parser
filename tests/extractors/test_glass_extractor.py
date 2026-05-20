from app.parsers.extractors.glass_extractor import (
    extract_glass
)


TEST_CASES = [

    "Pakiet 3 szyby Ug=0.5",

    "Okno dwuszybowe",

    "Szyba P4",

    "Lustro weneckie",

    "Ornament mleczny",

    "Ug 0.7",
]


for text in TEST_CASES:

    result = extract_glass(
        text
    )

    print()
    print(text)

    print(result)