from app.services.build_template_key import (
    build_template_key
)

construction = {

    "segments": [

        {
            "kind": "RU"
        },

        {
            "kind": "RU"
        }
    ]
}

key = build_template_key(
    construction
)

print(key)