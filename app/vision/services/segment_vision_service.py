from pathlib import Path
import base64

from dotenv import load_dotenv
from openai import OpenAI

from app.vision.prompts.segment_prompt import (
    SEGMENT_VISION_PROMPT
)

load_dotenv(
    dotenv_path=Path(".env")
)

client = OpenAI()


def analyze_segments_from_file(
    image_path: str
):

    with open(image_path, "rb") as f:

        base64_image = base64.b64encode(
            f.read()
        ).decode("utf-8")

    response = client.responses.create(

        model="gpt-4.1",

        temperature=0,

        input=[

            {
                "role": "system",
                "content": SEGMENT_VISION_PROMPT
            },

            {
                "role": "user",
                "content": [

                    {
                        "type": "input_text",
                        "text": (
                            "Analyze window segments."
                        )
                    },

                    {
                        "type": "input_image",
                        "image_url": (
                            f"data:image/jpeg;base64,"
                            f"{base64_image}"
                        )
                    }
                ]
            }
        ]
    )

    return response.output_text