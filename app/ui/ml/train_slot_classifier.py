import tensorflow as tf

from tensorflow.keras import layers
from tensorflow.keras import models

from tensorflow.keras.preprocessing.image import (
    ImageDataGenerator
)


IMAGE_SIZE = (64, 64)

BATCH_SIZE = 4

DATASET_DIR = "dataset"


train_datagen = ImageDataGenerator(

    rescale=1.0 / 255
)


train_generator = train_datagen.flow_from_directory(

    DATASET_DIR,

    target_size=IMAGE_SIZE,

    batch_size=BATCH_SIZE,

    class_mode="categorical"
)


model = models.Sequential([

    layers.Input(

        shape=(64, 64, 3)
    ),

    layers.Conv2D(

        16,

        (3, 3),

        activation="relu"
    ),

    layers.MaxPooling2D(

        (2, 2)
    ),

    layers.Conv2D(

        32,

        (3, 3),

        activation="relu"
    ),

    layers.MaxPooling2D(

        (2, 2)
    ),

    layers.Flatten(),

    layers.Dense(

        64,

        activation="relu"
    ),

    layers.Dense(

        train_generator.num_classes,

        activation="softmax"
    )
])


model.compile(

    optimizer="adam",

    loss="categorical_crossentropy",

    metrics=["accuracy"]
)


model.summary()


model.fit(

    train_generator,

    epochs=10
)


model.save(
    "models/slot_classifier.keras"
)


print(
    "[MODEL SAVED]"
)