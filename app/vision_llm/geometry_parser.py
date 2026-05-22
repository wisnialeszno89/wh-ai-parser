import json
import os

from dotenv import load_dotenv

from openai import OpenAI

from app.vision.utils.encode_image import (
    encode_image
)

from app.vision_llm.geometry_prompt import (
    GEOMETRY_PROMPT
)

load_dotenv()

client = OpenAI()


def parse_geometry(
    image_path: str
):

    base64_image = encode_image(
        image_path
    )

    response = client.responses.create(

        model=os.getenv(
            "MODEL",
            "gpt-4.1"
        ),

        input=[

            {
                "role": "system",
                "content": GEOMETRY_PROMPT
            },

            {
                "role": "user",

                "content": [

                    {
                        "type": "input_text",

                        "text": (
                            "Analyze window geometry."
                        )
                    },

                    {
                        "type": "input_image",

                        "image_url": (
                            f"data:image/png;base64,"
                            f"{base64_image}"
                        )
                    }
                ]
            }
        ]
    )

    text = response.output_text

    print("\nRAW RESPONSE:\n")
    print(text)

    text = text.replace(
    "```json",
    ""
    )

    text = text.replace(
    "```",
    ""
    )

    text = text.strip()

    return json.loads(text)