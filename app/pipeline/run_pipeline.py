from pathlib import Path
import json

from app.ai.vision_parser import (
    parse_image
)

from app.services.normalize_ai_output import (
    normalize_ai_output
)

from app.services.build_construction import (
    build_construction
)

from app.services.infer_segment_dimensions import (
    infer_segment_dimensions
)

from app.validator.semantic_validator import (
    validate_schema
)


def run_pipeline(image_path: str):

    # =====================================
    # AI PARSE
    # =====================================

    ai_result = parse_image(
        image_path
    )

    # =====================================
    # NORMALIZE RAW AI
    # =====================================

    normalized = normalize_ai_output(
        ai_result
    )

    # =====================================
    # BUILD TYPED SCHEMA
    # =====================================

    construction = build_construction(
        normalized
    )

    # =====================================
    # INFER GEOMETRY
    # =====================================

    construction = infer_segment_dimensions(
        construction
    )

    # =====================================
    # SEMANTIC VALIDATION
    # =====================================

    errors = validate_schema(
        construction
    )

    if errors:

        raise ValueError(
            f"Schema validation failed: {errors}"
        )

    # =====================================
    # SAVE OUTPUT
    # =====================================

    out_dir = Path(
        "outputs/normalized"
    )

    out_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    out_path = (
        out_dir / "result.json"
    )

    with open(
        out_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            construction,
            f,
            default=str,
            indent=2,
            ensure_ascii=False
        )

    return construction