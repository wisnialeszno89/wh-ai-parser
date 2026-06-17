import tensorflow as tf

from tensorflow.keras import layers
from tensorflow.keras import models


DATASET_PATH = (
    "dataset_v3"
)

IMAGE_SIZE = (
    64,
    64
)

BATCH_SIZE = 16

MODEL_PATH = (
    "models/semantic_classifier_v3.keras"
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
print("=" * 80)
print("CLASSES")
print("=" * 80)

for c in class_names:

    print(c)

print()
print("=" * 80)
print(
    f"TOTAL CLASSES: {len(class_names)}"
)
print("=" * 80)
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

print()
print("=" * 80)
print("TRAINING")
print("=" * 80)
print()

history = model.fit(

    train_ds,

    validation_data=val_ds,

    epochs=15
)


print()
print("=" * 80)
print("FINAL METRICS")
print("=" * 80)

print(
    f"train_acc = "
    f"{history.history['accuracy'][-1]:.4f}"
)

print(
    f"val_acc = "
    f"{history.history['val_accuracy'][-1]:.4f}"
)

print()


model.save(
    MODEL_PATH
)

print(
    f"[MODEL SAVED] {MODEL_PATH}"
)

print()