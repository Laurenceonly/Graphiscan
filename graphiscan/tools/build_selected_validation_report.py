"""Compile selected model versions' existing validation results; no training."""
import csv
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.local-tools/training-experiment-matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

EXPERIMENTS = ROOT / '.local-tools/training-experiments'
OUT = ROOT / 'output/selected-model-validation-2026-11-10'
SOURCES = {
    'MobileNetV2': ('finetune-20261110T005127Z', 'validation_before', 'Original'),
    'EfficientNetB0': ('finetune-EfficientNetB0-20261110T010325Z', 'validation_after', 'Fine-tuned'),
    'ResNet50': ('finetune-ResNet50-20261110T011424Z', 'validation_after', 'Fine-tuned'),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = {}
    for name, (folder, key, version) in SOURCES.items():
        source = json.loads((EXPERIMENTS / folder / 'results.json').read_text(encoding='utf-8'))
        entry = source[key]
        if entry['n'] != 134 or source['threshold'] != .75 or source['test_set_used']:
            raise ValueError('Unexpected experiment data')
        data[name] = {'version': version, 'evaluation': entry,
                      'artifact_sha256': source['source_model_sha256' if key.endswith('before') else 'artifact_sha256']}
        grid = np.asarray(entry['confusion_matrix'])
        fig, ax = plt.subplots(figsize=(6, 4.8))
        ax.imshow(grid, cmap='Blues')
        ax.set(title=name + ': validation matrix (0.75)', xlabel='Predicted', ylabel='Actual',
               xticks=[0, 1], yticks=[0, 1], xticklabels=['Normal', 'High Potential'], yticklabels=['Normal', 'High Potential'])
        for row in range(2):
            for col in range(2):
                ax.text(col, row, str(grid[row, col]), ha='center', va='center', color='white' if grid[row, col] > grid.max() / 2 else 'black')
        fig.tight_layout(); fig.savefig(OUT / (name + '_validation_confusion_matrix.png'), dpi=180); plt.close(fig)
        if key.endswith('after'):
            shutil.copyfile(EXPERIMENTS / folder / 'finetuning_accuracy_loss.png', OUT / (name + '_finetuning_accuracy_loss.png'))
    if len({row['evaluation']['dataset_sha256'] for row in data.values()}) != 1:
        raise ValueError('Validation sets differ')
    names = list(data)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(names, [data[name]['evaluation']['accuracy'] * 100 for name in names], color=['#3b6992', '#6089ac', '#88a7c1'])
    ax.bar_label(bars, fmt='%.2f%%', padding=3)
    ax.set(title='Selected models: validation accuracy (0.75 threshold)', ylabel='Validation accuracy (%)', ylim=(0, 105))
    fig.tight_layout(); fig.savefig(OUT / 'validation_accuracy_comparison.png', dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 5))
    keys = ['accuracy', 'high_potential_precision', 'high_potential_recall', 'high_potential_f1']
    labels = ['Accuracy', 'High Potential precision', 'High Potential recall', 'High Potential F1']
    x = np.arange(len(names))
    for i, (key, label) in enumerate(zip(keys, labels)):
        ax.bar(x + (i - 1.5) * .19, [data[name]['evaluation'][key] * 100 for name in names], .19, label=label)
    ax.set(title='Selected models: validation performance (0.75 threshold)', ylabel='Percent', ylim=(0, 105), xticks=x, xticklabels=names)
    ax.legend(fontsize=8, loc='upper center', bbox_to_anchor=(.5, -.15), ncol=2)
    fig.tight_layout(); fig.savefig(OUT / 'validation_performance_comparison.png', dpi=180); plt.close(fig)
    with (OUT / 'class_metrics.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['model', 'selected_version', 'validation_accuracy_percent', 'class', 'precision_percent', 'recall_percent', 'f1_percent'])
        for name, item in data.items():
            for label, metrics in item['evaluation']['per_class'].items():
                writer.writerow([name, item['version'], round(item['evaluation']['accuracy'] * 100, 2), label,
                                 *(round(metrics[k] * 100, 2) for k in ('precision', 'recall', 'f1'))])
    (OUT / 'selected_results.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
    print('Selected validation report created:', OUT)


if __name__ == '__main__':
    main()
