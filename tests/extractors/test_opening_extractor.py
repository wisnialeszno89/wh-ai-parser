from app.parsers.extractors.opening_extractor import (
    extract_segments
)


TEST_CASES = [

    "FIX RU",

    "RU RU",

    "FIX/FIX/RU",

    "R U",

    "FIX | RU",
]


for text in TEST_CASES:

    result = extract_segments(
        text
    )

    print()

    print(text)

    print(result)