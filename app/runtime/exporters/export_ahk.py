def export_ahk(

    commands,

    output_path
):

    lines = []

    for cmd in commands:

        if cmd.command_type == "click":

            lines.append(

                f"MouseMove, "
                f"{cmd.x}, "
                f"{cmd.y}"
            )

            lines.append(
                "Click"
            )

            lines.append("")

        elif cmd.command_type == "mouse_drag":

            lines.append(

                f"; drag to "
                f"{cmd.x}, {cmd.y}"
            )

            lines.append("")

    script = "\n".join(
        lines
    )

    with open(

        output_path,

        "w",

        encoding="utf-8"

    ) as f:

        f.write(script)

    print(

        f"[EXPORT] saved AHK: "
        f"{output_path}"
    )