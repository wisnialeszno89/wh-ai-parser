import os

import pytest

from app.ai.vision_parser import parse_image


@pytest.mark.integration
def test_parse_image():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is required for vision integration test")

    result = parse_image(
        "tests/assets/images/sample_01.jpg"
    )

    assert result is not None
