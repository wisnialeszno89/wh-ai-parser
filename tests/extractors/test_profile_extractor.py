from app.parsers.extractors.profile_extractor import (
    extract_profile
)


TEST_CASES = [

    "Okno VEKA Softline 82",

    "HST Aluplast",

    "Drzwi Salamander",

    "PSK Gealan S9000",

    "Schuco AWS 75",

    "VEKA Motion",
]


for text in TEST_CASES:

    result = extract_profile(
        text
    )

    print()
    print(text)

    print(result)