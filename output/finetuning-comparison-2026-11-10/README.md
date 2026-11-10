# Fine-tuning comparison — 10 November 2026

Each experiment started from its corresponding existing binary model, fine-tuned up to the last 20 backbone layers (batch-normalization layers remained frozen), used learning rate 0.00001 for up to three epochs, and restored the weights with best validation loss. All comparisons below use the same 134 validation images and a 0.75 High Potential threshold, with RGB/Pillow preparation. The test set was not used in these fine-tuning experiments.

| Model | Accuracy before | Accuracy after | High Potential identified before | High Potential identified after | False positives before → after |
| --- | ---: | ---: | ---: | ---: | ---: |
| MobileNetV2 | 118/134 (88.06%) | 117/134 (87.31%) | 53/65 (81.54%) | 50/65 (76.92%) | 4 → 2 |
| EfficientNetB0 | 106/134 (79.10%) | 112/134 (83.58%) | 38/65 (58.46%) | 45/65 (69.23%) | 1 → 2 |
| ResNet50 | 101/134 (75.37%) | 115/134 (85.82%) | 32/65 (49.23%) | 51/65 (78.46%) | 0 → 5 |

Fine-tuned ResNet50 and EfficientNetB0 improved on this validation set; ResNet50 also produced five more false positives. Fine-tuned MobileNetV2 missed three additional High Potential samples despite two fewer false positives. The original MobileNetV2 remained the highest-accuracy model on this validation set. These numbers are validation results, not test results, and must not be mixed with the previous 136-image test table.

Training/validation accuracy and loss figures and before/after confusion matrices are in the model-named folders. The epoch curves use TensorFlow's dataset image resizing; before/after matrices use the current RGB/Pillow evaluation preparation. Each accuracy curve and matrix uses a 0.75 threshold. Confusion-matrix rows are actual labels and columns are predictions.

The validation set was used for early stopping and has been used in prior work. Writer separation is not verified. A new independent, writer-separated evaluation is needed before drawing conclusions about performance on new students. These are screening outputs, not diagnoses. The app's models and catalogue were not changed.
