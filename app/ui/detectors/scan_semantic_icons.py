import os
import cv2
import numpy as np

from tensorflow.keras.models import (
    load_model
)


MODEL_PATH = (
    "models/slot_classifier.keras"
)


CLASS_NAMES = [

    "frame_tool",

    "glass_tool",

    "mullion_tool",

    "sash_tool",

    "slope_tool",

    "unknown"
]


OUTPUT_PATH = (
    "outputs/debug_semantic_icons.png"
)


WINDOW_SIZE = 64

STEP = 24

CONFIDENCE_THRESHOLD = 0.45


model = load_model(
    MODEL_PATH
)


def scan_semantic_icons(

    image_path: str
):

    image = cv2.imread(
        image_path
    )

    height, width, _ = image.shape

    debug = image.copy()

    candidates = []

    positions = []

    for y in range(

        0,

        height - WINDOW_SIZE,

        STEP
    ):

        for x in range(

            0,

            width - WINDOW_SIZE,

            STEP
        ):

            crop = image[

                y:y + WINDOW_SIZE,

                x:x + WINDOW_SIZE
            ]

            crop = cv2.resize(

                crop,

                (64, 64)
            )

            crop = crop.astype(
                "float32"
            ) / 255.0

            candidates.append(
                crop
            )

            positions.append({

                "x": x,

                "y": y
            })

    batch = np.array(
        candidates
    )

    predictions = model.predict(

        batch,

        verbose=1
    )

    detections = []

    for i, prediction in enumerate(

        predictions
    ):

        class_index = np.argmax(
            prediction
        )

        confidence = float(

            prediction[class_index]
        )

        predicted_class = (

            CLASS_NAMES[class_index]
        )

        x = positions[i]["x"]

        y = positions[i]["y"]
        print(

        f"[SCAN] "

        f"{predicted_class} "

        f"{confidence:.4f} "

        f"x={x} "

        f"y={y}"
        )
        if (

            predicted_class != "unknown"

            and

            confidence >= CONFIDENCE_THRESHOLD
        ):

            detections.append({

                "x": x,

                "y": y,

                "class": predicted_class,

                "confidence": confidence
            })

            cv2.rectangle(

                debug,

                (x, y),

                (

                    x + WINDOW_SIZE,

                    y + WINDOW_SIZE
                ),

                (0, 255, 0),

                2
            )

            cv2.putText(

                debug,

                predicted_class,

                (

                    x,

                    y - 5
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.5,

                (0, 255, 0),

                1
            )

            print(

                f"[ICON] "

                f"{predicted_class} "

                f"{confidence:.4f} "

                f"x={x} "

                f"y={y}"
            )

    os.makedirs(

        "outputs",

        exist_ok=True
    )

    cv2.imwrite(

        OUTPUT_PATH,

        debug
    )

    print(
        f"[SAVED] {OUTPUT_PATH}"
    )

    return detections