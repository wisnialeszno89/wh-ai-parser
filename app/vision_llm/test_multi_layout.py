from app.vision_llm.geometry_parser import (
    parse_geometry
)

result = parse_geometry(
    "training_data/multi_layout/page_1.png"
)

print("\nPARSED:\n")
print(result)