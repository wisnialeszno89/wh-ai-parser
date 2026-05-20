from app.parsers.text_offer_parser import (
    parse_offer_text
)


TEXT = """

VEKA Softline 82

Szer. x Wys. [mm]: 2090 x 1440

DKL/DKR mit festem Pfosten

Ug=0.5

"""


schema = parse_offer_text(
    TEXT
)


print(schema)