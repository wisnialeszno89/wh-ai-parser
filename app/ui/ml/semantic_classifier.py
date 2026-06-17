import os
import cv2
import numpy as np
import tensorflow as tf


MODEL_PATH = "models/semantic_classifier_v2.keras"
DATASET_PATH = "dataset_augmented"


class SemanticClassifier:

    def __init__(self):

        self.model = tf.keras.models.load_model(
            MODEL_PATH
        )

        self.class_names = sorted(
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

        print(
            f"[CLASSIFIER] loaded "
            f"{len(self.class_names)} classes"
        )

    def predict_crop(
        self,
        crop
    ):

        image = cv2.resize(
            crop,
            (64, 64)
        )

        image = image.astype(
            np.float32
        )

        image = np.expand_dims(
            image,
            axis=0
        )

        predictions = self.model.predict(
            image,
            verbose=0
        )[0]

        top_indices = np.argsort(
            predictions
        )[::-1][:3]

        top3 = []

        for idx in top_indices:

            top3.append({

                "tool":
                    self.class_names[idx],

                "confidence":
                    float(
                        predictions[idx]
                    )
            })

        best = top3[0]

        return (

            best["tool"],

            best["confidence"],

            top3
        )