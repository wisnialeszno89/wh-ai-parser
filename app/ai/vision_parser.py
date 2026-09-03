import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from app.ai.prompt import VISION_SYSTEM_PROMPT
from app.utils.json_extractor import extract_json
from app.vision.utils.encode_image import encode_image


load_dotenv(dotenv_path=Path(".env"))


def _client() -> OpenAI:
    return OpenAI()


def _parse_image(image_url: str):
    response = _client().responses.create(
        model=os.getenv("MODEL", "gpt-4.1"),
        input=[
            {
                "role": "system",
                "content": VISION_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Przeanalizuj konstrukcję i zwróć JSON.",
                    },
                    {
                        "type": "input_image",
                        "image_url": image_url,
                    },
                ],
            },
        ],
    )

    return extract_json(response.output_text)


def parse_image_url(image_url: str):
    return _parse_image(image_url)


def parse_image(image_path: str):
    path = Path(image_path)

    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    base64_image = encode_image(str(path))

    suffix = path.suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    mime_type = mime_types.get(suffix, "application/octet-stream")

    return _parse_image(
        f"data:{mime_type};base64,{base64_image}"
    )
