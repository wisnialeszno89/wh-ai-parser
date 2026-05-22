import json
import os

from dotenv import load_dotenv

from openai import OpenAI

from app.vision.utils.encode_image import (
    encode_image
)

from app.vision_llm.multi_layout_prompt import (
    MULTI_LAYOUT_PROMPT
)

load_dotenv()

client = OpenAI()


def parse_multi_layout(
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

                "content": (
                    MULTI_LAYOUT_PROMPT
                )
            },

            {
                "role": "user",

                "content": [

                    {
                        "type": "input_text",

                        "text": (
                            "Analyze ALL constructions "
                            "visible on the page."
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

    data = json.loads(text)

    constructions = data.get(
        "constructions",
        []
    )

    normalized = []

    for c in constructions:

        category = (
            c.get(
                "category",
                "WINDOW"
            )
        )

        confidence = float(
            c.get(
                "confidence",
                0.0
            )
        )

        width_mm = int(
            c.get(
                "width_mm",
                0
            )
        )

        height_mm = int(
            c.get(
                "height_mm",
                0
            )
        )

        segments = []

        for s in c.get(
            "segments",
            []
        ):

            kind = (
                s.get(
                    "kind",
                    "FIX"
                )
                .upper()
                .strip()
            )

            if kind not in [
                "FIX",
                "R",
                "RU"
            ]:
                kind = "FIX"

            segments.append({

                "kind": kind
            })

        normalized.append({

            "category": category,

            "width_mm": width_mm,

            "height_mm": height_mm,

            "confidence": confidence,

            "segments": segments
        })

    return normalized