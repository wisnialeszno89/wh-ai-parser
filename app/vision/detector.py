def is_technical_window_image(ai_response: str) -> bool:
    text = ai_response.lower()

    keywords = [
        "window",
        "fix",
        "ru",
        "dimensions",
        "technical drawing",
        "segment"
    ]

    return any(k in text for k in keywords)