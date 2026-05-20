import os

from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from app.ai.prompt import (
    VISION_SYSTEM_PROMPT
)

from app.utils.json_extractor import (
    extract_json
)

load_dotenv(
    dotenv_path=Path(".env")
)

client = OpenAI()


def parse_image_url(image_url: str):

    response = client.responses.create(

        model=os.getenv(
            "MODEL",
            "gpt-4.1"
        ),

        input=[

            {
                "role": "system",
                "content": VISION_SYSTEM_PROMPT
            },

            {
                "role": "user",
                "content": [

                    {
                        "type": "input_text",
                        "text": (
                            "Przeanalizuj konstrukcję "
                            "i zwróć JSON."
                        )
                    },

                    {
                        "type": "input_image",
                        "image_url": image_url
                    }
                ]
            }
        ]
    )

    content = response.output_text

    return extract_json(content)