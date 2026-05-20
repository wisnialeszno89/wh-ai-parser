from app.vision.services.geometry_vision_service import (
    analyze_geometry
)

IMAGE_URL = "https://i.imgur.com/AUTGT7J.jpeg"

result = analyze_geometry(
    IMAGE_URL
)

print(result)