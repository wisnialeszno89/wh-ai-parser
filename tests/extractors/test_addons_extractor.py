from app.parsers.extractors.addons_extractor import (
    extract_addons
)


TEST_CASES = [

    "Okno z roleta",

    "Moskitiera i parapet",

    "Nawiewnik",

    "Cieply montaz Illbruck",
]


for text in TEST_CASES:

    result = extract_addons(
        text
    )

    print()
    print(text)

    print(result)