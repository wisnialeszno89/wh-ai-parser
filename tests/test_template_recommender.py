from app.parsers.semantic_offer_parser import (
    parse_offer_text
)

from app.services.template_recommender import (
    recommend_template
)


TEXT = """
FIX RU
2120x1460
"""


schema = parse_offer_text(
    TEXT
)


result = recommend_template(

    schema,

    "fix_ru"
)


print()
print(result)