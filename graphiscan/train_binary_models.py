import csv
import json
import os
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score
)
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint


# =========================================================
# GRAPHISCAN BINARY TRANSFER LEARNING TRAINING
# Models:
#   1. MobileNetV2
#   2. EfficientNetB0
#   3. ResNet50
#
# Classes:
#   normal = 0
#   high_potential = 1
# =========================================================


# =========================================================
# 1. PATHS
# =========================================================

BASE_DIR = Path(r"C:\capstone\graphiscan")
DATASET_DIR = BASE_DIR / "binary_dataset"

TRAIN_DIR = DATASET_DIR / "train"
VAL_DIR = DATASET_DIR / "validation"
TEST_DIR = DATASET_DIR / "test"

OUTPUT_DIR = BASE_DIR / "training_results"
MODEL_OUTPUT_DIR = OUTPUT_DIR / "models"
GRAPH_OUTPUT_DIR = OUTPUT_DIR / "graphs"

FINAL_MODEL_DIR = BASE_DIR / "model"
FINAL_MODEL_PATH = FINAL_MODEL_DIR / "graphiscan_model.keras"
FINAL_CLASS_NAMES_PATH = FINAL_MODEL_DIR / "class_names.json"
FINAL_MODEL_CONFIG_PATH = FINAL_MODEL_DIR / "model_config.json"

CLASS_NAMES = ["normal", "high_potential"]


# =========================================================
# 2. TRAINING SETTINGS
# =========================================================

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 8
EPOCHS = 5
SEED = 42


# =========================================================
# 3. SETUP
# =========================================================

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GRAPH_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FINAL_MODEL_DIR.mkdir(parents=True, exist_ok=True)

print("\n" + "=" * 70)
print("GRAPHISCAN Binary Transfer Learning Training")
print("=" * 70)
print("TensorFlow:", tf.__version__)
print("Dataset:", DATASET_DIR)
print("Output:", OUTPUT_DIR)
print("Models: MobileNetV2, EfficientNetB0, ResNet50")
print("Classes:", CLASS_NAMES)
print("normal = 0")
print("high_potential = 1")
print("=" * 70 + "\n")


def check_dataset_structure():
    required_paths = [
        TRAIN_DIR / "normal",
        TRAIN_DIR / "high_potential",
        VAL_DIR / "normal",
        VAL_DIR / "high_potential",
        TEST_DIR / "normal",
        TEST_DIR / "high_potential"
    ]

    for folder in required_paths:
        if not folder.exists():
            raise FileNotFoundError(f"Missing required folder: {folder}")

    image_extensions = {".jpg", ".jpeg", ".png"}

    for split_name, split_dir in [
        ("train", TRAIN_DIR),
        ("validation", VAL_DIR),
        ("test", TEST_DIR)
    ]:
        print(f"\n{split_name.upper()} SET")

        for class_name in CLASS_NAMES:
            class_dir = split_dir / class_name
            image_count = len([
                file for file in class_dir.iterdir()
                if file.suffix.lower() in image_extensions
            ])

            print(f"{class_name}: {image_count} images")

            if image_count == 0:
                raise ValueError(f"No images found in: {class_dir}")


check_dataset_structure()


# =========================================================
# 4. LOAD DATASET
# =========================================================

train_ds = tf.keras.utils.image_dataset_from_directory(
    str(TRAIN_DIR),
    labels="inferred",
    label_mode="binary",
    class_names=CLASS_NAMES,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=True,
    seed=SEED
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    str(VAL_DIR),
    labels="inferred",
    label_mode="binary",
    class_names=CLASS_NAMES,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=False
)

test_ds = tf.keras.utils.image_dataset_from_directory(
    str(TEST_DIR),
    labels="inferred",
    label_mode="binary",
    class_names=CLASS_NAMES,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=False
)

AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.prefetch(AUTOTUNE)
val_ds = val_ds.prefetch(AUTOTUNE)
test_ds = test_ds.prefetch(AUTOTUNE)


# =========================================================
# 5. AUGMENTATION
# =========================================================

data_augmentation = tf.keras.Sequential(
    [
        layers.RandomRotation(0.05),
        layers.RandomZoom(0.08),
        layers.RandomTranslation(0.05, 0.05),
        layers.RandomContrast(0.08)
    ],
    name="data_augmentation"
)


# =========================================================
# 6. MODEL BUILDERS
# =========================================================

def add_binary_head(base_model, model_name, preprocessing_layer=None):
    base_model.trainable = False

    inputs = layers.Input(shape=(224, 224, 3), name="input_image")

    x = data_augmentation(inputs)

    if preprocessing_layer is not None:
        x = preprocessing_layer(x)

    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D(name="global_average_pooling")(x)
    x = layers.Dense(128, activation="relu", name="dense_features")(x)
    x = layers.Dropout(0.35, name="dropout")(x)

    outputs = layers.Dense(1, activation="sigmoid", name="binary_output")(x)

    model = models.Model(inputs, outputs, name=model_name)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="binary_crossentropy",
        metrics=["accuracy"]
    )

    return model


def build_mobilenetv2():
    base_model = tf.keras.applications.MobileNetV2(
        include_top=False,
        weights="imagenet",
        input_shape=(224, 224, 3)
    )

    preprocessing_layer = layers.Rescaling(
        scale=1.0 / 127.5,
        offset=-1.0,
        name="mobilenetv2_preprocess"
    )

    return add_binary_head(
        base_model=base_model,
        model_name="MobileNetV2",
        preprocessing_layer=preprocessing_layer
    )


def build_efficientnetb0():
    base_model = tf.keras.applications.EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_shape=(224, 224, 3)
    )

    # EfficientNet in Keras expects raw 0 to 255 image values.
    # Its preprocessing is already part of the application model.
    return add_binary_head(
        base_model=base_model,
        model_name="EfficientNetB0",
        preprocessing_layer=None
    )


def build_resnet50():
    base_model = tf.keras.applications.ResNet50(
        include_top=False,
        weights="imagenet",
        input_shape=(224, 224, 3)
    )

    preprocessing_layer = layers.Lambda(
        tf.keras.applications.resnet50.preprocess_input,
        name="resnet50_preprocess"
    )

    return add_binary_head(
        base_model=base_model,
        model_name="ResNet50",
        preprocessing_layer=preprocessing_layer
    )


MODELS_TO_TRAIN = {
    "MobileNetV2": build_mobilenetv2,
    "EfficientNetB0": build_efficientnetb0,
    "ResNet50": build_resnet50
}


# =========================================================
# 7. TRAINING + EVALUATION HELPERS
# =========================================================

def plot_training_graphs(model_name, history):
    accuracy_path = GRAPH_OUTPUT_DIR / f"{model_name}_accuracy.png"
    loss_path = GRAPH_OUTPUT_DIR / f"{model_name}_loss.png"

    plt.figure(figsize=(7, 5))
    plt.plot(history.history["accuracy"], label="Training Accuracy")
    plt.plot(history.history["val_accuracy"], label="Validation Accuracy")
    plt.title(f"{model_name} Accuracy")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.grid(True)
    plt.savefig(accuracy_path, dpi=300, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(7, 5))
    plt.plot(history.history["loss"], label="Training Loss")
    plt.plot(history.history["val_loss"], label="Validation Loss")
    plt.title(f"{model_name} Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.grid(True)
    plt.savefig(loss_path, dpi=300, bbox_inches="tight")
    plt.close()


def evaluate_model(model):
    y_true = []
    y_pred = []

    for images, labels in test_ds:
        probabilities = model.predict(images, verbose=0).reshape(-1)
        predictions = (probabilities >= 0.5).astype(int)

        y_true.extend(labels.numpy().reshape(-1).astype(int))
        y_pred.extend(predictions)

    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    matrix = confusion_matrix(y_true, y_pred)

    return y_true, y_pred, accuracy, precision, recall, f1, matrix


def plot_confusion_matrix(model_name, matrix):
    cm_path = GRAPH_OUTPUT_DIR / f"{model_name}_confusion_matrix.png"

    plt.figure(figsize=(5, 4))
    plt.imshow(matrix)
    plt.title(f"{model_name} Confusion Matrix")
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.xticks([0, 1], ["Normal", "High Potential"])
    plt.yticks([0, 1], ["Normal", "High Potential"])

    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            plt.text(col, row, matrix[row, col], ha="center", va="center")

    plt.savefig(cm_path, dpi=300, bbox_inches="tight")
    plt.close()


def save_results_csv(results):
    csv_path = OUTPUT_DIR / "model_comparison_results.csv"

    fieldnames = [
        "Model",
        "Accuracy",
        "Precision",
        "Recall",
        "F1 Score",
        "Model Path"
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    return csv_path


# =========================================================
# 8. TRAIN ALL MODELS
# =========================================================

results = []

for model_name, build_function in MODELS_TO_TRAIN.items():
    print("\n" + "=" * 70)
    print(f"Training {model_name}")
    print("=" * 70)

    model = build_function()
    model_path = MODEL_OUTPUT_DIR / f"{model_name}_best.keras"

    callbacks = [
        EarlyStopping(
            monitor="val_loss",
            patience=2,
            restore_best_weights=True
        ),
        ModelCheckpoint(
            str(model_path),
            monitor="val_loss",
            save_best_only=True
        )
    ]

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=callbacks
    )

    y_true, y_pred, accuracy, precision, recall, f1, matrix = evaluate_model(model)

    print("\nTest Results:", model_name)
    print("Accuracy:", round(accuracy, 4))
    print("Precision:", round(precision, 4))
    print("Recall:", round(recall, 4))
    print("F1 Score:", round(f1, 4))
    print("Confusion Matrix:")
    print(matrix)
    print(
        classification_report(
            y_true,
            y_pred,
            target_names=["Normal", "High Potential"],
            zero_division=0
        )
    )

    plot_training_graphs(model_name, history)
    plot_confusion_matrix(model_name, matrix)

    results.append(
        {
            "Model": model_name,
            "Accuracy": accuracy,
            "Precision": precision,
            "Recall": recall,
            "F1 Score": f1,
            "Model Path": str(model_path)
        }
    )


# =========================================================
# 9. SAVE COMPARISON RESULTS
# =========================================================

results = sorted(
    results,
    key=lambda item: (item["F1 Score"], item["Accuracy"]),
    reverse=True
)

csv_path = save_results_csv(results)

print("\n" + "=" * 70)
print("FINAL MODEL COMPARISON")
print("=" * 70)

for row in results:
    print(
        row["Model"],
        "| Accuracy:", round(row["Accuracy"], 4),
        "| Precision:", round(row["Precision"], 4),
        "| Recall:", round(row["Recall"], 4),
        "| F1:", round(row["F1 Score"], 4)
    )


# Accuracy comparison graph
plt.figure(figsize=(8, 5))
plt.bar([row["Model"] for row in results], [row["Accuracy"] for row in results])
plt.title("Model Accuracy Comparison")
plt.xlabel("Model")
plt.ylabel("Test Accuracy")
plt.ylim(0, 1)
plt.grid(axis="y")
plt.savefig(GRAPH_OUTPUT_DIR / "model_accuracy_comparison.png", dpi=300, bbox_inches="tight")
plt.close()


# Metrics comparison graph
x = np.arange(len(results))
width = 0.2

plt.figure(figsize=(9, 5))
plt.bar(x - 0.3, [row["Accuracy"] for row in results], width, label="Accuracy")
plt.bar(x - 0.1, [row["Precision"] for row in results], width, label="Precision")
plt.bar(x + 0.1, [row["Recall"] for row in results], width, label="Recall")
plt.bar(x + 0.3, [row["F1 Score"] for row in results], width, label="F1 Score")
plt.xticks(x, [row["Model"] for row in results])
plt.ylim(0, 1)
plt.title("Model Performance Comparison")
plt.xlabel("Model")
plt.ylabel("Score")
plt.legend()
plt.grid(axis="y")
plt.savefig(GRAPH_OUTPUT_DIR / "model_metrics_comparison.png", dpi=300, bbox_inches="tight")
plt.close()


# =========================================================
# 10. COPY BEST MODEL TO SYSTEM MODEL FOLDER
# =========================================================

best_model = results[0]
best_model_name = best_model["Model"]
best_model_path = Path(best_model["Model Path"])

shutil.copy2(best_model_path, FINAL_MODEL_PATH)

with open(FINAL_CLASS_NAMES_PATH, "w", encoding="utf-8") as file:
    json.dump(CLASS_NAMES, file)

with open(FINAL_MODEL_CONFIG_PATH, "w", encoding="utf-8") as file:
    json.dump(
        {
            "model_name": best_model_name,
            "classes": CLASS_NAMES,
            "input_size": [224, 224],
            "threshold": 0.75,
            "normal_label": 0,
            "high_potential_label": 1
        },
        file,
        indent=2
    )

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
print("Best model:", best_model_name)
print("Best model copied to:", FINAL_MODEL_PATH)
print("Class names saved to:", FINAL_CLASS_NAMES_PATH)
print("Model config saved to:", FINAL_MODEL_CONFIG_PATH)
print("Results CSV:", csv_path)
print("Graphs folder:", GRAPH_OUTPUT_DIR)
print("Model outputs folder:", MODEL_OUTPUT_DIR)
print("=" * 70)
