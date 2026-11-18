# Model figures for the manuscript

These figures use the selected original MobileNetV2 and the selected fine-tuned EfficientNetB0 and ResNet50. The comparison figures show the previously used 136-image test split at a 0.75 High Potential threshold. The test images were used in earlier comparisons, writer separation has not been verified, and the results are not independent clinical validation.

## Figures ready to insert

- `MobileNetV2_archived_accuracy_loss.png`: the two archived MobileNetV2 training and validation plots combined without recreating their values. Suggested caption: **Archived MobileNetV2 training and validation accuracy and loss.** See the provenance qualification below.
- `EfficientNetB0_finetuning_accuracy_loss.png`: training and validation accuracy and loss during the selected EfficientNetB0's three-epoch fine-tuning run. Suggested caption: **Training and validation accuracy and loss during EfficientNetB0 fine-tuning.**
- `ResNet50_finetuning_accuracy_loss.png`: equivalent graphs for the selected ResNet50 fine-tuning run. Suggested caption: **Training and validation accuracy and loss during ResNet50 fine-tuning.**
- `test_accuracy_comparison.png`: overall test accuracy for the three selected versions. Suggested caption: **Overall test accuracy of the selected CNN models.**
- `test_classification_performance.png`: precision, recall and F1-score for each class and selected version. Suggested caption: **Class-specific test precision, recall and F1-score of the selected CNN models.** Bar labels are rounded to one decimal place; tables report two.
- `test_confusion_matrices.png`: classification counts for the three selected versions. Suggested caption: **Test confusion matrices for the selected CNN models.** Rows are actual dataset labels and columns are predicted labels.

Number captions according to their final position in the document. Replace the existing graphics rather than placing these next to old graphics with conflicting results. Check each figure reference, caption and page layout after insertion.

The supplied `Graphiscan (5).pdf` uses this intended sequence: Figure 18 MobileNetV2 accuracy/loss, Figure 19 EfficientNetB0 accuracy/loss, Figure 20 ResNet50 accuracy/loss, Figure 21 accuracy comparison, and Figure 22 performance comparison. The five corresponding files above cover that sequence, subject to the MobileNetV2 provenance qualification. The confusion-matrix image is an additional optional figure and requires its own caption and figure number if inserted. The current document's images and figure numbers must be rechecked after the replacements, because editing can change layout and numbering.

## MobileNetV2 training graph: provenance qualification

The saved `training_results/models/MobileNetV2_best.keras` has the same SHA-256 as the selected MobileNetV2 artifact in the recorded test result. The archived accuracy/loss plots were saved in the same training-results tree immediately after that model's checkpoint; the training script writes the graphs from its training history after saving the checkpoint. This is supporting evidence that the graphs belong to the original training workflow, but the underlying history and a graph-to-checkpoint hash were not preserved, so the link is not independently proven. Verify the original run records if available before presenting the graph as definitive evidence. The archived training accuracy uses the historical 0.50 metric threshold, not the 0.75 test threshold. The separate three-epoch MobileNetV2 fine-tuning experiment used a different, unselected model and is not included.

## Interpretation and table check

| Selected version | Test accuracy | High Potential precision | High Potential recall | High Potential F1 |
|---|---:|---:|---:|---:|
| Original MobileNetV2 | 85.29% | 91.07% | 77.27% | 83.61% |
| Fine-tuned EfficientNetB0 | 78.68% | 89.36% | 63.64% | 74.34% |
| Fine-tuned ResNet50 | 86.76% | 96.15% | 75.76% | 84.75% |

The test class-metric CSV is included as `test_class_metrics.csv`. In the live manuscript, the earlier class-metric table and Table 11 were checked against these results and include overall accuracy. Table 11 explains that the first row for each model is Normal and the second is High Potential. The earlier table may split across pages; check its layout in the final document.

The fine-tuning charts are **training and validation histories**, not test results; their epoch accuracy uses a 0.75 threshold, and the history was measured using TensorFlow resizing. The final comparison uses runtime-style Pillow preparation. The selected fine-tuned weights were restored based on validation loss, so the last epoch is not necessarily the selected checkpoint. The validation set was also used in model selection. Do not describe either curve as independent test performance.

The existing live manuscript graphics still need to be replaced and their captions reconciled. A previously reviewed manuscript's MobileNet figure matched a separate fine-tuning experiment and must not be presented as the selected original model's history. The existing earlier PDF export has not been updated.

Sources: `graphiscan/training_results/graphs/MobileNetV2_accuracy.png` and `MobileNetV2_loss.png`; `graphiscan/train_binary_models.py`; `output/selected-model-test-2026-11-10/results.json` and `model_classification_results.csv`; `output/finetuning-comparison-2026-11-10/EfficientNetB0/results.json` and `ResNet50/results.json`. No new training or model evaluation was performed to make these figures.
