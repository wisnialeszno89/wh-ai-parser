import tensorflow as tf

from tensorflow.keras import layers
from tensorflow.keras import models


DATASET_PATH = (
    "dataset_augmented"
)

IMAGE_SIZE = (
    64,
    64
)

BATCH_SIZE = 16

MODEL_PATH = (
    "models/semantic_classifier_v2.keras"
)


train_ds = tf.keras.utils.image_dataset_from_directory(

    DATASET_PATH,

    validation_split=0.2,

    subset="training",

    seed=123,

    image_size=IMAGE_SIZE,

    batch_size=BATCH_SIZE
)

val_ds = tf.keras.utils.image_dataset_from_directory(

    DATASET_PATH,

    validation_split=0.2,

    subset="validation",

    seed=123,

    image_size=IMAGE_SIZE,

    batch_size=BATCH_SIZE
)

class_names = train_ds.class_names

print()

print("[CLASSES]")

for c in class_names:

    print(c)

print()


model = models.Sequential([

    layers.Rescaling(
        1.0 / 255
    ),

    layers.Conv2D(
        32,
        3,
        activation="relu"
    ),

    layers.MaxPooling2D(),

    layers.Conv2D(
        64,
        3,
        activation="relu"
    ),

    layers.MaxPooling2D(),

    layers.Flatten(),

    layers.Dense(
        128,
        activation="relu"
    ),

    layers.Dense(
        len(class_names),
        activation="softmax"
    )
])

model.compile(

    optimizer="adam",

    loss="sparse_categorical_crossentropy",

    metrics=["accuracy"]
)

model.summary()

model.fit(

    train_ds,

    validation_data=val_ds,

    epochs=15
)

model.save(
    MODEL_PATH
)

print()
print(
    "[MODEL SAVED]"
)
print(
    MODEL_PATH
)