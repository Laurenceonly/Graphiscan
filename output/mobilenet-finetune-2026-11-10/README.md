# MobileNetV2 fine-tuning experiment

This experiment continued training a separate copy of the existing MobileNetV2 for three epochs, with learning rate 0.00001. The last 20 backbone layers were eligible for training except batch-normalization layers, which remained frozen. Best validation-loss weights were restored. The app model was not replaced.

Both before and after were evaluated at a 0.75 High Potential threshold using the same 134 validation images (69 Normal and 65 High Potential), prepared with the current RGB/Pillow image path. The test set was not used in this experiment.

| Measure | Existing model | Fine-tuned copy |
| --- | ---: | ---: |
| Validation accuracy | 118/134 (88.06%) | 117/134 (87.31%) |
| High Potential recall | 53/65 (81.54%) | 50/65 (76.92%) |
| High Potential precision | 53/57 (92.98%) | 50/52 (96.15%) |
| False positives (Normal labeled High Potential) | 4 | 2 |
| False negatives (High Potential labeled Normal) | 12 | 15 |

Fine-tuning reduced false positives but missed three more High Potential samples and slightly reduced overall accuracy. This does not establish an improvement for screening. Keep the current model; the fine-tuned copy is not deployed.

This validation set has been used in training and model selection and is not independent clinical validation. Writer separation is not confirmed. Accuracy and loss graphs record the training epochs; training/validation metric curves use 0.75, while the before/after confusion matrices use the current RGB/Pillow preparation.

The script is `graphiscan/tools/finetune_mobile_experiment.py`. The separate trained model and detailed source hashes remain under `.local-tools/training-experiments/finetune-20261110T005127Z`.
