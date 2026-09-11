import os

import pytest

from app.ai.vision_parser import parse_image_url
from app.services.normalize_ai_output import normalize_ai_output


@pytest.mark.integration
def test_pipeline_from_image_url():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is required for pipeline integration test")

    result = parse_image_url(
        "https://i.imgur.com/0s7Ff7d.jpeg"
    )

    normalized = normalize_ai_output(
        result
    )

    assert normalized is not None
