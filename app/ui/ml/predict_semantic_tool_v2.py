import os
import cv2
import numpy as np
import tensorflow as tf


MODEL_PATH = (
    "models/semantic_classifier_v2.keras"
)

DATASET_PATH = (
    "dataset_augmented"
)


model = tf.keras.models.load_model(
    MODEL_PATH
)


class_names = sorted(
    [
        d
        for d in os.listdir(
            DATASET_PATH
        )
        if os.path.isdir(
            os.path.join(
                DATASET_PATH,
                d
            )
        )
    ]
)


def predict_semantic_tool(
    image_path: str
):

    image = cv2.imread(
        image_path
    )

    if image is None:

        print(
            f"[ERROR] File not found: {image_path}"
        )

        return

    image = cv2.resize(
        image,
        (64, 64)
    )

    image = image.astype(
        np.float32
    )

    image = np.expand_dims(
        image,
        axis=0
    )

    predictions = model.predict(
        image,
        verbose=0
    )[0]

    top_indices = np.argsort(
        predictions
    )[::-1][:3]

    print()
    print(
        f"[FILE] {image_path}"
    )
    print()

    for rank, idx in enumerate(
        top_indices,
        start=1
    ):

        print(
            f"TOP {rank}: "
            f"{class_names[idx]} "
            f"{predictions[idx]:.4f}"
        )

    print()


if __name__ == "__main__":

    import os

    slots = sorted(
        os.listdir(
            "outputs/toolbar_slots"
        )
    )

    for slot in slots:

        predict_semantic_tool(
            os.path.join(
                "outputs/toolbar_slots",
                slot
            )
        )