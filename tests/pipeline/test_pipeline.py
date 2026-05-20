from app.ai.vision_parser import (
    parse_image_url
)

from app.services.normalize_ai_output import (
    normalize_ai_output
)


result = parse_image_url(
    "https://i.imgur.com/0s7Ff7d.jpeg"
)

normalized = normalize_ai_output(
    result
)

print("\n========== RESULT ==========\n")

print(normalized)