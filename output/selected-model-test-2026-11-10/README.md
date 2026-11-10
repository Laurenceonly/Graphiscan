# Selected model versions — previously used test set

The selected original MobileNetV2, fine-tuned EfficientNetB0 and fine-tuned ResNet50 were measured on the existing 136-image test split, at the deployed 0.75 threshold using the runtime-style EXIF/RGB/Pillow image path. Artifact hashes for the two fine-tuned versions were checked against the training records. The original MobileNetV2 result exactly matches its prior Keras test confusion matrix.

| Selected model | Correct / 136 | Test accuracy | High Potential identified / 66 | False positives |
| --- | ---: | ---: | ---: | ---: |
| MobileNetV2, original | 116 | 85.29% | 51 | 5 |
| EfficientNetB0, fine-tuned | 107 | 78.68% | 42 | 5 |
| ResNet50, fine-tuned | 118 | 86.76% | 50 | 2 |

The test images were used in earlier model comparisons, and writer-level separation is unverified. This is not an independent or clinical evaluation. Test accuracy differs from the selected versions' 134-image validation accuracy; do not mix those figures. The selected fine-tuned versions have not been converted, parity-checked on the hosted LiteRT runtime, registered, deployed or accepted on a device.

Class-level precision, recall and F1 are in `model_classification_results.csv` as fractions. Confusion-matrix rows are actual classes; columns are predicted classes. Models are screening aids and do not diagnose dysgraphia.
