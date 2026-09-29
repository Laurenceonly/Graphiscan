import gc
import json
import shutil
from pathlib import Path

import numpy as np
import tensorflow as tf

from sklearn.metrics import classification_report, confusion_matrix

from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

from tensorflow.keras.applications import MobileNetV2, EfficientNetB0, ResNet50V2


# =========================================================
# CONFIG
# =========================================================

DATASET_DIR = Path("dataset_image_split")
MODEL_DIR = Path("model")
CANDIDATE_DIR = MODEL_DIR / "candidates"
REPORT_DIR = MODEL_DIR / "reports"

FINAL_MODEL_PATH = MODEL_DIR / "graphiscan_model.keras"
CLASS_NAMES_PATH = MODEL_DIR / "class_names.json"
MODEL_INFO_PATH = MODEL_DIR / "model_info.json"

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 16

EPOCHS_HEAD = 10
EPOCHS_FINE_TUNE = 5

FINE_TUNE_LAST_LAYERS = 30

CLASS_NAMES = [
    "normal",
    "low_potential_dysgraphia",
    "high_potential_dysgraphia"
]

MODEL_OPTIONS = {
    "MobileNetV2": MobileNetV2,
    "EfficientNetB0": EfficientNetB0,
    "ResNet50V2": ResNet50V2
}


# =========================================================
# DATASET
# =========================================================

def load_datasets():
    train_ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR / "train",
        class_names=CLASS_NAMES,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="categorical",
        shuffle=True,
        seed=42
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR / "validation",
        class_names=CLASS_NAMES,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="categorical",
        shuffle=False
    )

    test_ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR / "test",
        class_names=CLASS_NAMES,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="categorical",
        shuffle=False
    )

    autotune = tf.data.AUTOTUNE

    train_ds = train_ds.prefetch(autotune)
    val_ds = val_ds.prefetch(autotune)
    test_ds = test_ds.prefetch(autotune)

    return train_ds, val_ds, test_ds


def get_class_weights():
    counts = {}

    for index, class_name in enumerate(CLASS_NAMES):
        folder = DATASET_DIR / "train" / class_name
        image_count = len([
            item for item in folder.iterdir()
            if item.is_file()
        ])
        counts[index] = image_count

    total = sum(counts.values())
    number_of_classes = len(CLASS_NAMES)

    class_weights = {}

    for class_index, count in counts.items():
        class_weights[class_index] = total / (number_of_classes * count)

    print("\nClass weights:")
    for class_index, weight in class_weights.items():
        print(f"{CLASS_NAMES[class_index]}: {weight:.4f}")

    return class_weights


# =========================================================
# MODEL BUILDER
# =========================================================

def build_model(model_name):
    base_model_class = MODEL_OPTIONS[model_name]

    inputs = layers.Input(shape=(224, 224, 3))

    x = layers.RandomRotation(0.03)(inputs)
    x = layers.RandomZoom(0.08)(x)
    x = layers.RandomTranslation(0.05, 0.05)(x)
    x = layers.RandomContrast(0.10)(x)

    if model_name in ["MobileNetV2", "ResNet50V2"]:
        x = layers.Rescaling(1.0 / 127.5, offset=-1.0)(x)

    base_model = base_model_class(
        include_top=False,
        weights="imagenet",
        input_shape=(224, 224, 3)
    )

    base_model.trainable = False

    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.35)(x)
    outputs = layers.Dense(len(CLASS_NAMES), activation="softmax")(x)

    model = models.Model(inputs, outputs, name=model_name)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.0005),
        loss="categorical_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall")
        ]
    )

    return model, base_model


def fine_tune_model(model, base_model):
    base_model.trainable = True

    for layer in base_model.layers[:-FINE_TUNE_LAST_LAYERS]:
        layer.trainable = False

    for layer in base_model.layers:
        if isinstance(layer, layers.BatchNormalization):
            layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.00005),
        loss="categorical_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall")
        ]
    )

    return model


# =========================================================
# EVALUATION
# =========================================================

def evaluate_model(model, test_ds, model_name):
    y_true = []
    y_pred = []

    for images, labels in test_ds:
        predictions = model.predict(images, verbose=0)

        y_true.extend(np.argmax(labels.numpy(), axis=1))
        y_pred.extend(np.argmax(predictions, axis=1))

    report = classification_report(
        y_true,
        y_pred,
        target_names=CLASS_NAMES,
        output_dict=True,
        zero_division=0
    )

    report_text = classification_report(
        y_true,
        y_pred,
        target_names=CLASS_NAMES,
        zero_division=0
    )

    matrix = confusion_matrix(y_true, y_pred)

    print(f"\nClassification Report: {model_name}")
    print(report_text)

    print(f"\nConfusion Matrix: {model_name}")
    print(matrix)

    report_path = REPORT_DIR / f"{model_name}_classification_report.json"
    matrix_path = REPORT_DIR / f"{model_name}_confusion_matrix.json"

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    with open(matrix_path, "w", encoding="utf-8") as file:
        json.dump(matrix.tolist(), file, indent=2)

    return {
        "model_name": model_name,
        "accuracy": report["accuracy"],
        "macro_f1": report["macro avg"]["f1-score"],
        "weighted_f1": report["weighted avg"]["f1-score"],
        "high_potential_recall": report["high_potential_dysgraphia"]["recall"],
        "report_path": str(report_path),
        "matrix_path": str(matrix_path)
    }


# =========================================================
# TRAINING
# =========================================================

def train_one_model(model_name, train_ds, val_ds, test_ds, class_weights):
    print("\n=================================================")
    print(f"Training model: {model_name}")
    print("=================================================\n")

    candidate_path = CANDIDATE_DIR / f"{model_name}.keras"

    model, base_model = build_model(model_name)

    callbacks = [
        EarlyStopping(
            monitor="val_loss",
            patience=4,
            restore_best_weights=True
        ),
        ModelCheckpoint(
            candidate_path,
            monitor="val_accuracy",
            save_best_only=True,
            mode="max",
            verbose=1
        )
    ]

    print("\nPhase 1: Training classifier head...\n")

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS_HEAD,
        callbacks=callbacks,
        class_weight=class_weights
    )

    print("\nPhase 2: Fine-tuning top layers...\n")

    model = fine_tune_model(model, base_model)

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS_FINE_TUNE,
        callbacks=callbacks,
        class_weight=class_weights
    )

    print("\nLoading best saved model...\n")
    best_model = tf.keras.models.load_model(candidate_path)

    metrics = evaluate_model(best_model, test_ds, model_name)

    del model
    del best_model
    gc.collect()
    tf.keras.backend.clear_session()

    return metrics


def pick_best_model(all_metrics):
    sorted_models = sorted(
        all_metrics,
        key=lambda item: (
            item["accuracy"],
            item["macro_f1"],
            item["high_potential_recall"]
        ),
        reverse=True
    )

    return sorted_models[0]


def save_final_outputs(best_model_info, all_metrics):
    best_model_name = best_model_info["model_name"]
    best_model_path = CANDIDATE_DIR / f"{best_model_name}.keras"

    if FINAL_MODEL_PATH.exists():
        FINAL_MODEL_PATH.unlink()

    shutil.copy2(best_model_path, FINAL_MODEL_PATH)

    with open(CLASS_NAMES_PATH, "w", encoding="utf-8") as file:
        json.dump(CLASS_NAMES, file, indent=2)

    final_info = {
        "selected_model": best_model_name,
        "input_size": [224, 224],
        "class_names": CLASS_NAMES,
        "selection_rule": "Highest test accuracy, then macro F1, then high potential dysgraphia recall",
        "best_metrics": best_model_info,
        "all_metrics": all_metrics
    }

    with open(MODEL_INFO_PATH, "w", encoding="utf-8") as file:
        json.dump(final_info, file, indent=2)

    summary_path = REPORT_DIR / "metrics_summary.json"

    with open(summary_path, "w", encoding="utf-8") as file:
        json.dump(all_metrics, file, indent=2)

    print("\n=================================================")
    print("BEST MODEL SELECTED")
    print("=================================================")
    print(f"Selected model: {best_model_name}")
    print(f"Final model saved to: {FINAL_MODEL_PATH}")
    print(f"Class names saved to: {CLASS_NAMES_PATH}")
    print(f"Model info saved to: {MODEL_INFO_PATH}")
    print(f"Metrics summary saved to: {summary_path}")


def main():
    if not all((DATASET_DIR / split).is_dir() for split in ("train", "validation", "test")):
        raise FileNotFoundError(
            f"Three-class split not found at {DATASET_DIR}. "
            "Create the image-level split using scripts/split_dataset.py."
        )
    MODEL_DIR.mkdir(exist_ok=True)
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nGRAPHISCAN 3-Class Model Training")
    print("Classes:")
    for index, class_name in enumerate(CLASS_NAMES):
        print(f"{index}: {class_name}")

    train_ds, val_ds, test_ds = load_datasets()
    class_weights = get_class_weights()

    all_metrics = []

    for model_name in MODEL_OPTIONS.keys():
        metrics = train_one_model(
            model_name,
            train_ds,
            val_ds,
            test_ds,
            class_weights
        )

        all_metrics.append(metrics)

    best_model_info = pick_best_model(all_metrics)
    save_final_outputs(best_model_info, all_metrics)


if __name__ == "__main__":
    main()
