from app.ui.dataset.export_toolbar_slots import (
    export_toolbar_slots
)

from app.ui.ml.predict_slot import (
    predict_slot
)


IMAGE = (
    "samples/zmieniony_wh_screen.png"
)


export_toolbar_slots(
    IMAGE
)


for i in range(27):

    slot_path = (
        f"outputs/toolbar_slots/"
        f"slot_{i}.png"
    )

    print(
        f"\n--- SLOT {i} ---"
    )

    predict_slot(
        slot_path
    )