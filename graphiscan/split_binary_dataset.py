import os
import random
import shutil
from pathlib import Path

RAW_DIR = Path(r"C:\capstone\graphiscan\binary_raw")
OUTPUT_DIR = Path(r"C:\capstone\graphiscan\binary_dataset")

CLASS_NAMES = ["normal", "high_potential"]

TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

random.seed(42)

if OUTPUT_DIR.exists():
    shutil.rmtree(OUTPUT_DIR)

for split in ["train", "validation", "test"]:
    for class_name in CLASS_NAMES:
        (OUTPUT_DIR / split / class_name).mkdir(parents=True, exist_ok=True)

for class_name in CLASS_NAMES:
    class_folder = RAW_DIR / class_name

    if not class_folder.exists():
        raise FileNotFoundError(f"Missing folder: {class_folder}")

    images = [
        file for file in class_folder.iterdir()
        if file.suffix.lower() in IMAGE_EXTENSIONS
    ]

    random.shuffle(images)

    total = len(images)
    train_end = int(total * TRAIN_RATIO)
    validation_end = train_end + int(total * VALIDATION_RATIO)

    split_files = {
        "train": images[:train_end],
        "validation": images[train_end:validation_end],
        "test": images[validation_end:]
    }

    for split, files in split_files.items():
        for file in files:
            destination = OUTPUT_DIR / split / class_name / file.name
            shutil.copy2(file, destination)

    print(f"{class_name}:")
    print(f"  train: {len(split_files['train'])}")
    print(f"  validation: {len(split_files['validation'])}")
    print(f"  test: {len(split_files['test'])}")

print("\nDone. Dataset is ready for training.")
print(OUTPUT_DIR)