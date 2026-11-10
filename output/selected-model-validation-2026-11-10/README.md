# Selected model comparison — validation results

This package presents the three versions selected by the user: the existing MobileNetV2, the fine-tuned EfficientNetB0, and the fine-tuned ResNet50. Their metrics were measured on the same 134 validation images at a 0.75 High Potential threshold with RGB/Pillow image preparation. They are validation results, not test results.

| Selected model | Correct / 134 | Validation accuracy | High Potential precision | High Potential recall | High Potential F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| MobileNetV2, original | 118 | 88.06% | 92.98% | 81.54% | 86.89% |
| EfficientNetB0, fine-tuned | 112 | 83.58% | 95.74% | 69.23% | 80.36% |
| ResNet50, fine-tuned | 115 | 85.82% | 91.07% | 78.46% | 84.30% |

The validation accuracy and performance comparison charts and `class_metrics.csv` use these selected versions and the same 0.75 validation evaluation. Each confusion matrix has actual labels in rows and predicted labels in columns. There are 69 Normal and 65 High Potential samples in the validation set. The selected versions were chosen after observing this set, and the two fine-tuned models also used it to select weights. These numbers are therefore not independent estimates of generalization; do not describe them as test accuracy or clinical validation. Writer-level separation is not established.

The EfficientNetB0 and ResNet50 training/validation graphs show their separate three-epoch fine-tuning runs, whose epoch accuracy uses 0.75. Their epoch curves use TensorFlow dataset resizing; the final validation comparison above uses the app-style Pillow path. MobileNetV2 is the existing model, so this package does not include a new training curve for it.

The existing MobileNetV2 is already represented by the current app model family. The selected fine-tuned EfficientNetB0 and ResNet50 are separate local experimental artifacts and are not installed in the app. The app's model catalogue still displays its existing recorded test accuracies, not these validation figures. No model, API, database or app release was changed by making this package. Before deployment or claiming final performance, conduct a properly documented evaluation on an independent writer-separated dataset; the previous test split has already been used in earlier experiments.
