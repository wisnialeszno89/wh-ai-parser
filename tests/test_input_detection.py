from app.services.input.load_input import (
    detect_input_type
)


TESTS = [

    "offer.pdf",

    "whatsapp.jpg",

    "client.txt",

    "scan.webp",
]


for item in TESTS:

    print()
    print(item)

    print(
        detect_input_type(item)
    )