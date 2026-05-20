import os

from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from app.vision.prompts.geometry_prompt import (
    GEOMETRY_VISION_PROMPT
)

load_dotenv(
    dotenv_path=Path(".env")
)

client = OpenAI()


def analyze_geometry(image_url: str):

    response = client.responses.create(

        model="gpt-4.1",

        temperature=0,

        input=[

            {
                "role": "system",
                "content": GEOMETRY_VISION_PROMPT
            },

            {
                "role": "user",
                "content": [

                    {
                        "type": "input_text",
                        "text": (
                            "Analyze technical window geometry."
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

    return response.output_text