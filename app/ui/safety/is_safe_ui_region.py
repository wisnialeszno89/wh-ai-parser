def is_safe_ui_region(

    x,
    y,

    screen_width,
    screen_height
):

    top_right_zone = (

        x > screen_width - 120
        and
        y < 60
    )

    if top_right_zone:

        return False

    return True