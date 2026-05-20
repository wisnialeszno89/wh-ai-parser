from app.ai.vision_parser import parse_image


result = parse_image(
    "tests/assets/images/sample_01.jpg"
)

print(result)