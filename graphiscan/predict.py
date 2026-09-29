import os
import json
import numpy as np
from PIL import Image

import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.resnet50 import preprocess_input as resnet50_preprocess_input
from tensorflow.keras.applications.resnet_v2 import preprocess_input as resnet50v2_preprocess_input


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "graphiscan_model.keras")
CLASS_NAMES_PATH = os.path.join(BASE_DIR, "model", "class_names.json")

IMG_SIZE = (224, 224)

_loaded_model = None
_class_names = None


def load_class_names():
    if not os.path.exists(CLASS_NAMES_PATH):
        return ["high_potential", "normal"]

    with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as file:
        names = json.load(file)

    if isinstance(names, dict):
        names = list(names.values())

    return [str(name).strip().lower() for name in names]


def load_graphiscan_model():
    global _loaded_model
    global _class_names

    if _loaded_model is not None:
        return _loaded_model

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

    _class_names = load_class_names()

    custom_objects = {
        "preprocess_input": resnet50_preprocess_input
    }

    try:
        _loaded_model = load_model(
            MODEL_PATH,
            compile=False,
            safe_mode=False,
            custom_objects=custom_objects
        )
    except Exception:
        custom_objects = {
            "preprocess_input": resnet50v2_preprocess_input
        }

        _loaded_model = load_model(
            MODEL_PATH,
            compile=False,
            safe_mode=False,
            custom_objects=custom_objects
        )

    return _loaded_model


def prepare_image(image_path):
    image = Image.open(image_path).convert("RGB")
    image = image.resize(IMG_SIZE)

    image_array = np.array(image).astype("float32")
    image_array = np.expand_dims(image_array, axis=0)

    return image_array


def get_high_potential_probability(prediction):
    global _class_names

    prediction = np.array(prediction)

    if prediction.ndim == 2:
        prediction = prediction[0]

    if prediction.ndim == 0:
        score = float(prediction)
        return score

    if len(prediction) == 1:
        score = float(prediction[0])

        if _class_names and len(_class_names) >= 2:
            positive_label = _class_names[1]

            if "normal" in positive_label:
                return 1.0 - score

            if "high" in positive_label or "potential" in positive_label:
                return score

        return score

    high_index = None
    normal_index = None

    for index, class_name in enumerate(_class_names or []):
        clean_name = str(class_name).lower()

        if "high" in clean_name or "potential" in clean_name:
            high_index = index

        if "normal" in clean_name:
            normal_index = index

    if high_index is not None and high_index < len(prediction):
        return float(prediction[high_index])

    if normal_index is not None and normal_index < len(prediction):
        return 1.0 - float(prediction[normal_index])

    return float(np.max(prediction))


def classify_result(high_probability):
    high_percentage = round(high_probability * 100, 2)
    normal_percentage = round((1.0 - high_probability) * 100, 2)

    if high_probability >= 0.75:
        classification = "High Potential"
        confidence_score = high_percentage
    else:
        classification = "Normal"
        confidence_score = normal_percentage

    return {
        "classification": classification,
        "dysgraphia_probability": high_percentage,
        "high_potential_probability": high_percentage,
        "normal_probability": normal_percentage,
        "confidence_score": confidence_score,
        "analysis_summary": ""
    }


def predict_handwriting(image_path):
    print("\n--- GRAPHISCAN BINARY PREDICTION DEBUG ---")
    print("Image path:", image_path)
    print("Model path:", MODEL_PATH)
    print("Model exists:", os.path.exists(MODEL_PATH))
    print("Class names path:", CLASS_NAMES_PATH)
    print("Class names exists:", os.path.exists(CLASS_NAMES_PATH))

    model = load_graphiscan_model()
    image_array = prepare_image(image_path)

    prediction = model.predict(image_array, verbose=0)
    high_probability = get_high_potential_probability(prediction)

    result = classify_result(high_probability)

    print("Raw prediction:", prediction)
    print("Class names:", _class_names)
    print("Final classification:", result["classification"])
    print("High potential probability:", result["high_potential_probability"])

    return result
