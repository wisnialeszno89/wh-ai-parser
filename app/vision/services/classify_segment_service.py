import base64

from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from app.vision.prompts.classify_segment_prompt import (
    CLASSIFY_SEGMENT_PROMPT
)

load_dotenv(
    dotenv_path=Path(".env")
)

client = OpenAI()


def classify_segment(
    image_path: str
):

    with open(image_path, "rb") as f:

        base64_image = base64.b64encode(
            f.read()
        ).decode("utf-8")

    response = client.responses.create(

        model="gpt-4.1-mini",

        temperature=0,

        input=[

            {
                "role": "system",
                "content": CLASSIFY_SEGMENT_PROMPT
            },

            {
                "role": "user",
                "content": [

                    {
                        "type": "input_text",
                        "text": (
                            "Classify window segment."
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