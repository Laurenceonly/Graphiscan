import os
import random
import shutil
from pathlib import Path

RAW_DATASET_DIR = Path("raw_dataset")
OUTPUT_DATASET_DIR = Path("dataset")

CLASS_NAMES = [
    "normal",
    "low_potential_dysgraphia",
    "high_potential_dysgraphia"
]

TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

RANDOM_SEED = 42


def is_image_file(file_path):
    return file_path.suffix.lower() in IMAGE_EXTENSIONS


def prepare_output_folders():
    if OUTPUT_DATASET_DIR.exists():
        shutil.rmtree(OUTPUT_DATASET_DIR)

    for split in ["train", "validation", "test"]:
        for class_name in CLASS_NAMES:
            folder_path = OUTPUT_DATASET_DIR / split / class_name
            folder_path.mkdir(parents=True, exist_ok=True)


def copy_files(files, split_name, class_name):
    target_folder = OUTPUT_DATASET_DIR / split_name / class_name

    for index, file_path in enumerate(files, start=1):
        new_name = f"{class_name}_{index:04d}{file_path.suffix.lower()}"
        shutil.copy2(file_path, target_folder / new_name)


def split_class_images(class_name):
    source_folder = RAW_DATASET_DIR / class_name

    if not source_folder.exists():
        raise FileNotFoundError(f"Missing folder: {source_folder}")

    image_files = [
        file_path
        for file_path in source_folder.iterdir()
        if file_path.is_file() and is_image_file(file_path)
    ]

    random.shuffle(image_files)

    total = len(image_files)

    train_count = int(total * TRAIN_RATIO)
    validation_count = int(total * VALIDATION_RATIO)

    train_files = image_files[:train_count]
    validation_files = image_files[train_count:train_count + validation_count]
    test_files = image_files[train_count + validation_count:]

    copy_files(train_files, "train", class_name)
    copy_files(validation_files, "validation", class_name)
    copy_files(test_files, "test", class_name)

    return {
        "class": class_name,
        "total": total,
        "train": len(train_files),
        "validation": len(validation_files),
        "test": len(test_files)
    }


def main():
    random.seed(RANDOM_SEED)

    print("\nPreparing dataset split...")
    prepare_output_folders()

    results = []

    for class_name in CLASS_NAMES:
        result = split_class_images(class_name)
        results.append(result)

    print("\nDataset split completed.\n")

    for result in results:
        print(f"{result['class']}")
        print(f"  total: {result['total']}")
        print(f"  train: {result['train']}")
        print(f"  validation: {result['validation']}")
        print(f"  test: {result['test']}\n")

    print("Final folder created: dataset/")


if __name__ == "__main__":
    main()