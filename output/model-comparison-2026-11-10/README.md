# Binary model experiment — 10 November 2026

This is a separate experiment, not the model currently installed in the app.
Each architecture started with ImageNet pretrained weights and a fresh classification head. The pretrained backbone was frozen. Each model trained for up to five epochs with the same augmentation and early stopping based on validation loss. All used the existing image-level split: 627 training, 134 validation and 136 test images. The classes were Normal and High Potential; Low Potential samples were excluded.

Test images were EXIF-normalized, converted to RGB and resized with Pillow, matching the current prediction preparation. Test predictions used a 0.75 High Potential threshold. Training and validation accuracy curves use Keras's 0.50 threshold, as labeled on the graphs; they must not be compared directly to test accuracy at 0.75.

| Model | Correct / 136 | Accuracy | High Potential precision | High Potential recall | High Potential F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| MobileNetV2 | 108 | 79.41% | 95.24% | 60.61% | 74.07% |
| EfficientNetB0 | 81 | 59.56% | 100.00% | 16.67% | 28.57% |
| ResNet50 | 112 | 82.35% | 95.65% | 66.67% | 78.57% |

High Potential recall is the share of the 66 test samples labeled High Potential that the model identified: MobileNetV2 40/66, EfficientNetB0 11/66, ResNet50 44/66. For example, the EfficientNetB0 precision of 100% reflects 11 correct High Potential predictions and zero false positives, but it missed 55 High Potential samples.

The classification CSV gives class-specific precision, recall and F1 as fractions, not percentages. Confusion-matrix rows are actual labels and columns are predicted labels. Training graphs show every epoch run; the saved model uses the best validation-loss weights.

Limitations: the same test set was used in prior experiments, so this is not a new independent test; writer separation is unverified; results are a single run on 136 test images and are not clinical validation. The models do not diagnose dysgraphia. Do not select, publish or replace a deployed model solely on these figures. Graphs and results are from this fresh run, not the older results in the paper.

The full experiment source is `graphiscan/tools/train_binary_experiment.py`; the trained files remain under `.local-tools/training-experiments/20261109T235516Z` (UTC timestamp). The app's existing models and catalogue were not changed.
