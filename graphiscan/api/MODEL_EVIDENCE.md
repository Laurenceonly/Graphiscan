# Existing binary model evidence

## Linux verification and serving kernel, 2026-10-24

The exact previously converted files were checked on Linux against all three
original TensorFlow models, without reconversion or quantization. MobileNetV2
and EfficientNetB0 used the CPU delegate; ResNet50 used the builtin CPU kernel
to reduce serving memory. All136 images per model passed: zero class changes,
identical matrices to both original references and prior Windows evidence.

| Model | Maximum absolute score difference | Class disagreements |
| --- | ---: | ---: |
| MobileNetV2 | 0.000008404 | 0/136 |
| EfficientNetB0 | 0.000006855 | 0/136 |
| ResNet50, builtin CPU | 0.000003636 | 0/136 |

The committed aggregate `litert-linux-evaluation.json` has SHA-256
`e9eb1beae81bb85ef0a24dd3349e646fd02ab0598017cbbcf84e8a3a1a324db1`.
Converted model hashes remain exactly those recorded below. Schema3's explicit
runtime kind and adapter hash bind the kernel selection; original Keras/source
pins and binary0.75 rule are unchanged. This remains the existing image split,
not independent/clinical/three-class evidence or verified writer separation.
Local serving-memory checks and real hosted workflow checks are separate gates.

## FP32 deployment-copy comparison, 2026-10-23

`tools/experiment_v1_lite_models.py --compare` completed on Windows using the
existing Python3.11.9/TensorFlow2.21.0/Keras3.14.1 and isolated LiteRT2.3.0 CPU.
Explicit inference (`training=False`) and raw weight-variable tracking excluded
training-only augmentation/cached functions from the export. No weights were
retrained or quantized. The same136-image split, EXIF-normalized PNG input,
PIL RGB224/raw float32 preprocessing and0.75 threshold were used for both paths.
Dataset SHA-256 remains
`29c3bb42a09a733eacc43489dcb9214d2b526aa1866e61114a93db943b744549`.

| Copy | Size MiB | Max absolute score difference | Class disagreements | Confusion matrix |
| --- | ---: | ---: | ---: | --- |
| MobileNetV2 | 9.10 | 0.000008613 | 0/136 | `[[65,5],[15,51]]` |
| EfficientNetB0 | 15.93 | 0.000007182 | 0/136 | `[[66,4],[33,33]]` |
| ResNet50 | 90.62 | 0.000009149 | 0/136 | `[[69,1],[36,30]]` |

All copied matrices equal their original references. The aggregate report is
ignored `.local-tools/lite-model-experiment/comparison.local.json`, SHA-256
`d3111d32d59c97e90e278c6f7ef434bb581bb2fe3f7b0cf029d93f049444c71c`.
Converted SHA-256 identities:

- MobileNetV2: `3abdc7ee4b2b6317631e1d29b652362515c163ff51d67fe84fedbbb4387c31f9`
- EfficientNetB0: `bdc6e8dd70061e5be9a0697da77992a19c87e34b7e9c3beeeabdc9d3d0532734`
- ResNet50: `e141366a992cacbe1db8b733e16acbaca8d0e5b03196d47040efd7ff0242c906`

These copies require new artifact/version identities; the original catalogue
and historical records remain unchanged. This comparison establishes observed
numerical/class parity on the existing split only. It adds no independent test
set, writer separation, clinical evidence, improved accuracy or three-class
support. Linux/hosted numeric, memory-limit and authenticated workflow checks
remain separate. No images or per-image predictions were exported or uploaded.

## Inspected on 2026-10-20

The supplied `training_results/model_comparison_results.csv` records these existing binary experiments (fractions converted to percentages):

| Model | Accuracy | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| ResNet50 | 86.0294% | 86.1538% | 84.8485% | 85.4962% |
| EfficientNetB0 | 75.0000% | 66.3265% | 98.4848% | 79.2683% |
| MobileNetV2 | 72.7941% | 64.6465% | 96.9697% | 77.5758% |

The active `model/graphiscan_model.keras` and `training_results/models/ResNet50_best.keras` have the same SHA-256: `9c6e2cd5b031a0ec07378d73089286ba1140707b5861652b7152c48d2bf20fbd`. The active class mapping is `[normal, high_potential]`. No three-class support or accuracy follows from this evidence. A Custom_CNN artifact/graphs exist but the supplied comparison CSV does not contain its metrics.

The ResNet50 confusion-matrix image shows `[[61,9],[10,56]]`, with true classes as rows and predicted classes as columns, Normal then High Potential. Its 136 examples and derived metrics agree with the CSV. The existing test directory has 70 Normal and 66 High Potential image files. Matching counts alone do not prove split independence or absence of leakage; writer separation remains unverified.

A separate content-hash scan counted 627 training, 134 validation and 136 test images, with zero exact-content intersections for train/validation, train/test and validation/test. This check does not detect transformed copies, same-writer overlap or other forms of leakage.

## Decision-rule mismatch

`train_binary_models.py` evaluates sigmoid scores with a 0.50 cutoff, uses TensorFlow dataset resizing, then writes a deployment configuration with a 0.75 cutoff. `predict.py` and the hosted runtime use 0.75 and PIL resizing. Therefore the historical 86.03% must not be presented as measured accuracy of the current hosted pipeline. Training scripts contain old absolute paths; they were inspected as source, never imported or executed for this review.

`tools/evaluate_v1_models.py --compare` evaluates the three existing binary artifacts on the local test split through hosted image normalization and current predictor preprocessing. It reports both 0.50 and 0.75 thresholds, aggregate confusion matrices/metrics, dataset content-and-label digest and artifact/source hashes. It does not train, publish a registry entry, change database data, upload images or export image names/per-image predictions. Its aggregate output is saved under ignored `training_results/hosted_runtime_evaluation.local.json`. This reevaluation is separate evidence and preserves the original CSV and weights.

Registry publication, runtime manifest configuration, authenticated upload and deployment require their own verification. These historical results do not satisfy the panel's planned three-class comparison.

## Executed hosted-path reevaluation, 2026-10-20

The local comparison completed successfully for all three artifacts and all 136 images, using the same normalization/PIL preprocessing and class mapping, with no training or database changes. Dataset content-and-label SHA-256: `29c3bb42a09a733eacc43489dcb9214d2b526aa1866e61114a93db943b744549`. Runtime source SHA-256: `0b116fd56ad452278116507c2c43dc5c7b8692ae275e714db8fd0a1c3d753443`.

| Model | Threshold | Accuracy | Precision | Recall | F1 | Confusion matrix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| ResNet50 | 0.50 | 83.0882% | 93.8776% | 69.6970% | 80.0000% | `[[67,3],[20,46]]` |
| ResNet50 | 0.75 | 72.7941% | 96.7742% | 45.4545% | 61.8557% | `[[69,1],[36,30]]` |
| EfficientNetB0 | 0.50 | 80.8824% | 82.2581% | 77.2727% | 79.6875% | `[[59,11],[15,51]]` |
| EfficientNetB0 | 0.75 | 72.7941% | 89.1892% | 50.0000% | 64.0777% | `[[66,4],[33,33]]` |
| MobileNetV2 | 0.50 | 80.8824% | 73.8095% | 93.9394% | 82.6667% | `[[48,22],[4,62]]` |
| MobileNetV2 | 0.75 | 85.2941% | 91.0714% | 77.2727% | 83.6066% | `[[65,5],[15,51]]` |

MobileNetV2 has the highest measured accuracy at the existing 0.75 rule on this split. The original 0.50 CSV ranking must not determine a default for this different pipeline. Even the new 0.50 metrics differ from the historical CSV: the execution paths differ, and the exact cause has not been isolated. These are observed results from the available split, not new independent or clinical validation. Preserve the original records rather than replacing them.

That reevaluation did not change the legacy active artifact or threshold. The following implementation stages the hosted model versions separately; legacy JSON and Flask paths still use their existing ResNet50 predictor. A fresh provider upload and authorized role/device flow are still required.

## Hosted version integration prepared, 2026-10-20

`v1_models.py` implements schema-v2 manifest loading and three fixed binary architectures. Each version uses a separately staged SHA-256-named artifact under ignored `model/versions`, exact version/preprocessing/rule/hash checks, private lazy-loading caches and serialized inference. It reuses `predict.prepare_image` and `classify_result`, validates one scalar sigmoid output and does not mutate the legacy global model/path/class mapping. Source and class-map hashes are pinned too. Old single-model manifests remain supported.

`tools/prepare_v1_model_catalogue.py` was run successfully: validates evaluation/artifact/source identities and matrix-derived accuracy, stages all three weights, creates the ignored server manifest, saves its path locally and generates `db/postgres/publish_binary_models.sql`. It does not connect to PostgreSQL. The SQL is prepared and UNAPPLIED: one image-level evaluation, three immutable model identities with measured 0.75 accuracies, and MobileNetV2 default. It retains writer_separation_verified=false and refuses to overwrite an existing different default, changed published metadata or a withdrawn model. Exact repeats retain the same rows.

The existing React hosted upload selector already consumes `/models`. Backend selection now resolves the requested registry model or default to its matching installed identity, then reserve repeats authoritative access/model/default checks. A completed exact retry still reaches durable replay after model withdrawal; no client path or artifact is trusted. Catalogue responses offer only installed, registry-selectable supported versions. No automatic legacy-to-hosted switch is made.

Publication verification: owner ran `tools/check_v1_model_catalogue.py` against the restarted API and supplied all12 passing checks, including all3 published/installed identities/evaluation accuracies, unique selectable MobileNetV2 default, anonymous denial and temporary Auth-session cleanup. Agent separately verified generated-image Storage put/get/public-route denial/delete without application database writes. Do not repeat SQL or setup. Populated authorized teacher uploads, expert review, parent release, production deployment and three-class work remain pending.
