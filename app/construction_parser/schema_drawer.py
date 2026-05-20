def draw_schema(construction):

    segments = construction.get("segments", [])

    top = "┌"
    middle = "│"
    bottom = "└"

    for i, s in enumerate(segments):

        label = s.get("type", "UNK")

        width = max(len(label) + 2, 7)

        top += "─" * width
        bottom += "─" * width

        middle += label.center(width)

        if i < len(segments) - 1:
            top += "┬"
            middle += "│"
            bottom += "┴"

    top += "┐"
    middle += "│"
    bottom += "┘"

    return "\n".join([
        top,
        middle,
        bottom
    ])