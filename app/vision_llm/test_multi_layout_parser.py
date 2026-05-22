from app.vision_llm.multi_layout_parser import (
    parse_multi_layout
)

result = parse_multi_layout(
    "training_data/multi_layout/page_1.png"
)

print("\nPARSED:\n")
print(result)