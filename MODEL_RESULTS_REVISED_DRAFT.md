# Results of Model Testing and Performance Metrics

This section presents the test results for the selected MobileNetV2, EfficientNetB0, and ResNet50 convolutional neural network (CNN) models. The evaluated versions were the original MobileNetV2, fine-tuned EfficientNetB0, and fine-tuned ResNet50. All three models classified handwriting images into two categories: Normal and High Potential. The same test images, runtime-style image preparation, and 0.75 High Potential classification threshold were used for the comparison.

The selected dataset contained 897 images: 627 for training, 134 for validation, and 136 for testing. The training split contained 323 Normal and 304 High Potential images; the validation split contained 69 Normal and 65 High Potential images; and the test split contained 70 Normal and 66 High Potential images. The test images had been used in earlier model comparisons, and separation by writer has not been verified. Therefore, the test results should not be interpreted as an independent clinical evaluation.

The models were assessed using accuracy and class-specific precision, recall, and F1-score. Confusion-matrix counts were used to examine how many images in each actual class were assigned to each predicted class. Table 11 presents the results for the 136-image test split. Overall accuracy is repeated for each class; precision, recall, and F1-score are reported separately for each class.

**Table 11. Test performance of the selected CNN models for handwriting-image classification**

| Model and selected version | Class | Overall test accuracy (%) | Precision (%) | Recall (%) | F1-score (%) |
| --- | --- | ---: | ---: | ---: | ---: |
| MobileNetV2, original | Normal | 85.29 | 81.25 | 92.86 | 86.67 |
| MobileNetV2, original | High Potential | 85.29 | 91.07 | 77.27 | 83.61 |
| EfficientNetB0, fine-tuned | Normal | 78.68 | 73.03 | 92.86 | 81.76 |
| EfficientNetB0, fine-tuned | High Potential | 78.68 | 89.36 | 63.64 | 74.34 |
| ResNet50, fine-tuned | Normal | 86.76 | 80.95 | 97.14 | 88.31 |
| ResNet50, fine-tuned | High Potential | 86.76 | 96.15 | 75.76 | 84.75 |

*Note.* The accuracy value is an overall test accuracy repeated for each class for readability; it is not a class-specific average. The deployed catalogue displays the stored ResNet50 accuracy as 86.77%, while 118/136 is 86.76% when calculated from the counts and rounded to two decimal places.

The selected MobileNetV2 correctly classified 65 of the 70 Normal images and 51 of the 66 High Potential images. It classified five Normal images as High Potential and 15 High Potential images as Normal. Its High Potential precision was 91.07%, recall was 77.27%, and F1-score was 83.61%.

The selected fine-tuned EfficientNetB0 correctly classified 65 of the 70 Normal images and 42 of the 66 High Potential images. It classified five Normal images as High Potential and 24 High Potential images as Normal. Its High Potential precision was 89.36%, recall was 63.64%, and F1-score was 74.34%.

The selected fine-tuned ResNet50 correctly classified 68 of the 70 Normal images and 50 of the 66 High Potential images. It classified two Normal images as High Potential and 16 High Potential images as Normal. Its High Potential precision was 96.15%, recall was 75.76%, and F1-score was 84.75%.

On this test split, ResNet50 had the highest overall accuracy and the fewest Normal images classified as High Potential among the three selected versions. MobileNetV2 identified one more High Potential image than ResNet50, giving it slightly higher High Potential recall. EfficientNetB0 identified fewer High Potential images than the other two models. These differences describe performance on this particular image split and should not be generalized to clinical populations without further evaluation.

## Summary of Findings

The selected ResNet50 achieved 86.76% test accuracy, followed by MobileNetV2 at 85.29% and EfficientNetB0 at 78.68%. The current model catalogue records ResNet50 as the default and provides all three selected models as choices. The 134-image validation comparison produced a different ranking: MobileNetV2 achieved 88.06%, EfficientNetB0 83.58%, and ResNet50 85.82%. Validation and test results serve different purposes and must be labeled separately.

The findings support describing ResNet50 as the default with the highest overall accuracy in the recorded selected-version test comparison. They do not establish diagnostic performance, clinical reliability, or an effect on referrals. GraphiScan provides preliminary handwriting-image screening results for review by an authorized expert; it does not diagnose dysgraphia.

## Figure reconciliation before insertion

- Training and validation accuracy/loss figures must come from the exact selected training runs and be labeled with the model version. The previously reviewed Figure 18 corresponded to a separate MobileNetV2 fine-tuning experiment, not the selected original model; replace or relabel it only after confirming its source. Verify the EfficientNetB0 and ResNet50 graph sources as well.
- Generate or select the comparison figures from the selected-version data. Label the dataset split and threshold. If Figure 21 is an accuracy comparison and Figure 22 is a class-metric comparison, ensure the inserted images and captions actually show those contents; do not reuse the earlier validation graphs with test-result captions.
- Show actual confusion matrices if discussing them as figures. Each matrix uses actual class as rows and predicted class as columns: MobileNetV2 `[[65, 5], [15, 51]]`; EfficientNetB0 `[[65, 5], [24, 42]]`; ResNet50 `[[68, 2], [16, 50]]`, ordered Normal then High Potential.

Source: `output/selected-model-test-2026-11-10/model_classification_results.csv`, `results.json`, and `README.md`; validation comparison in `output/selected-model-validation-2026-11-10/class_metrics.csv`; deployment/default checkpoint in `KNOWLEDGE.md`. The source data, not this draft, is authoritative for graph construction. The user is preparing figures separately.
