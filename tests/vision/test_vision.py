import os
from pathlib import Path

import pytest

from app.ai.vision_parser import parse_image


@pytest.mark.integration
def test_parse_image():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is required for vision integration test")

    image_path = Path(
        "tests/assets/images/sample_01.jpg"
    )

    if not image_path.is_file():
        pytest.skip(
            "Local vision fixture is not present: "
            "tests/assets/images/sample_01.jpg"
        )

    result = parse_image(
        str(image_path)
    )

    assert result is not None
