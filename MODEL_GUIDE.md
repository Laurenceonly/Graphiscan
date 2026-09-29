# GraphiScan model guide

## What the app runs now

`graphiscan/predict.py` loads `graphiscan/model/graphiscan_model.keras`. This is the **binary** Normal / High Potential model. Its `dysgraphia_probability` field is the model's High Potential score multiplied by 100. The runtime labels a sample High Potential at 75%; `graphiscan/model/model_config.json` records that same value but is not read by the runtime. The reported 86.03% test accuracy is from 136 binary test images, not a per-image probability. The 75% cutoff has not been validated in the project records reviewed so far.

## Three-class experiment

`raw_dataset/` contains 462 Normal, 417 Low Potential, and 435 High Potential JPGs. The images have sequential filenames and no participant IDs, so writer separation cannot be verified. `model/` contains **earlier experimental** three-class models and reports; ResNet50V2 recorded 72% accuracy on 200 images. Those files are not loaded by the app. Do not compare 72% and 86.03% as if they measure the same task.

For a new run, use only these two scripts from the repository root:

1. `py scripts/split_dataset.py` creates `dataset_image_split/` with a reproducible 70/15/15 split. It preserves original filenames and refuses to overwrite an existing split.
2. `py scripts/train_compare_models.py` trains MobileNetV2, EfficientNetB0, and ResNet50V2 on that same split, evaluates all three on the test portion, and selects the highest test accuracy. It writes private artifacts and per-class reports under `model/`.

The split is **by image**, not by child. Report this limitation and do not describe test accuracy as performance on unseen children. The source images, split, model files, and student uploads remain outside Git. Neither script has been run as part of this cleanup.

## Before changing the live app

Review the three-class confusion matrices and per-class precision/recall, especially Normal versus Low Potential. The model score has not been checked for probability calibration; do not present it as a clinical likelihood. Then update inference, storage, teacher model selection, mobile result wording, and expert validation together. Preserve old binary results as binary records. No live three-class deployment has happened yet.
