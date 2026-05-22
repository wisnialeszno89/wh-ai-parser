from app.vision_llm.geometry_parser import (
    parse_geometry
)

result = parse_geometry(
    "training_data/geometry/FIX_RU/FIX RU 1.png"
)

print("\nPARSED:\n")
print(result)