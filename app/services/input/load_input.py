from pathlib import Path


TEXT_EXTENSIONS = [

    ".txt"
]


IMAGE_EXTENSIONS = [

    ".png",
    ".jpg",
    ".jpeg",
    ".webp"
]


PDF_EXTENSIONS = [

    ".pdf"
]


def detect_input_type(
    path: str
):

    extension = Path(
        path
    ).suffix.lower()


    if extension in TEXT_EXTENSIONS:

        return "text"


    if extension in IMAGE_EXTENSIONS:

        return "image"


    if extension in PDF_EXTENSIONS:

        return "pdf"


    return "unknown"