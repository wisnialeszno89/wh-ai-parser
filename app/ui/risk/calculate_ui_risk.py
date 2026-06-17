HIGH_RISK_LABELS = [

    "close_button",

    "delete_button",

    "cancel_button"
]


def calculate_ui_risk(

    ui_object,

    screen_width,
    screen_height
):

    risk = 0.0

    if ui_object.label in HIGH_RISK_LABELS:

        risk += 0.9

    near_top_right = (

        ui_object.x > screen_width - 120
        and
        ui_object.y < 80
    )

    if near_top_right:

        risk += 0.5

    if risk > 1.0:

        risk = 1.0

    return risk