from pydantic import ValidationError

from app.models.construction import Construction


def validate_construction(data: dict):

    try:

        model = Construction(**data)

        return {
            "valid": True,
            "data": model.model_dump(),
            "errors": None
        }

    except ValidationError as e:

        return {
            "valid": False,
            "data": None,
            "errors": e.errors()
        }