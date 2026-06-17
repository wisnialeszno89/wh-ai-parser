import cv2
import numpy as np

from tensorflow.keras.models import (
    load_model
)


MODEL_PATH = "models/slot_classifier.keras"


CLASS_NAMES = [

    "frame_tool",

    "glass_tool",

    "mullion_tool",

    "sash_tool",

    "slope_tool",

    "unknown"
]


IMAGE_SIZE = (64, 64)


model = load_model(
    MODEL_PATH
)


def predict_slot(

    image_path: str
):

    image = cv2.imread(
        image_path
    )

    image = cv2.resize(

        image,

        IMAGE_SIZE
    )

    image = image.astype(
        "float32"
    ) / 255.0

    image = np.expand_dims(

        image,

        axis=0
    )

    predictions = model.predict(
        image,
        verbose=0
    )

    class_index = np.argmax(
        predictions
    )

    confidence = float(

        predictions[0][class_index]
    )

    predicted_class = (

        CLASS_NAMES[class_index]
    )

    print(
        f"[PREDICTED] "
        f"{predicted_class}"
    )

    print(
        f"[CONFIDENCE] "
        f"{confidence:.4f}"
    )

    return {

        "class": predicted_class,

        "confidence": confidence
    }