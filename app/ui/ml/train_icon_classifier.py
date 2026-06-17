import tensorflow as tf

from tensorflow.keras import layers
from tensorflow.keras import models

from tensorflow.keras.preprocessing.image import (
    ImageDataGenerator
)


IMAGE_SIZE = (24, 24)

BATCH_SIZE = 8

EPOCHS = 10


train_datagen = ImageDataGenerator(

    rescale=1.0 / 255,

    validation_split=0.2
)


train_generator = train_datagen.flow_from_directory(

    "dataset",

    target_size=IMAGE_SIZE,

    batch_size=BATCH_SIZE,

    class_mode="categorical",

    subset="training",

    color_mode="grayscale"
)


validation_generator = train_datagen.flow_from_directory(

    "dataset",

    target_size=IMAGE_SIZE,

    batch_size=BATCH_SIZE,

    class_mode="categorical",

    subset="validation",

    color_mode="grayscale"
)


model = models.Sequential([

    layers.Input(shape=(24, 24, 1)),

    layers.Conv2D(

        16,

        (3, 3),

        activation="relu"
    ),

    layers.MaxPooling2D((2, 2)),

    layers.Conv2D(

        32,

        (3, 3),

        activation="relu"
    ),

    layers.MaxPooling2D((2, 2)),

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

    validation_data=validation_generator,

    epochs=EPOCHS
)


model.save(

    "models/icon_classifier.keras"
)

print(
    "[MODEL SAVED]"
)