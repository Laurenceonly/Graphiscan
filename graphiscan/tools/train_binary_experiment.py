"""Isolated three-model binary experiment. Does not publish or replace app models."""
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
os.environ.setdefault('KERAS_HOME', str(Path(__file__).resolve().parents[2] / '.local-tools' / 'training-experiment-keras'))
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[2] / '.local-tools' / 'training-experiment-matplotlib'))
import numpy as np
from PIL import Image, ImageOps
import tensorflow as tf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'binary_dataset'
OUT_ROOT = ROOT.parent / '.local-tools' / 'training-experiments'
CLASSES = ['normal', 'high_potential']
SEED = 42


def dataset(split, shuffle=False):
    return tf.keras.utils.image_dataset_from_directory(
        DATA / split, class_names=CLASSES, label_mode='binary', image_size=(224, 224),
        batch_size=8, shuffle=shuffle, seed=SEED, verbose=False).prefetch(1)


def build(name):
    constructors = {'MobileNetV2': tf.keras.applications.MobileNetV2,
                    'EfficientNetB0': tf.keras.applications.EfficientNetB0,
                    'ResNet50': tf.keras.applications.ResNet50}
    base = constructors[name](include_top=False, weights='imagenet', input_shape=(224, 224, 3))
    base.trainable = False
    inputs = tf.keras.Input(shape=(224, 224, 3))
    x = tf.keras.Sequential([tf.keras.layers.RandomRotation(.05), tf.keras.layers.RandomZoom(.08),
                             tf.keras.layers.RandomTranslation(.05, .05), tf.keras.layers.RandomContrast(.08)])(inputs)
    if name == 'MobileNetV2':
        x = tf.keras.layers.Rescaling(1 / 127.5, offset=-1)(x)
    elif name == 'ResNet50':
        x = tf.keras.layers.Lambda(tf.keras.applications.resnet50.preprocess_input)(x)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dense(128, activation='relu')(x)
    x = tf.keras.layers.Dropout(.35)(x)
    model = tf.keras.Model(inputs, tf.keras.layers.Dense(1, activation='sigmoid')(x), name=name)
    model.compile(optimizer=tf.keras.optimizers.Adam(.001), loss='binary_crossentropy', metrics=['accuracy'])
    return model


def evaluate(model, split='test'):
    matrix = [[0, 0], [0, 0]]
    digest = hashlib.sha256()
    entries = []
    for actual, label in enumerate(CLASSES):
        for path in (DATA / split / label).iterdir():
            if path.suffix.lower() in {'.jpg', '.jpeg', '.png'}:
                entries.append((actual, hashlib.sha256(path.read_bytes()).hexdigest(), path))
    for actual, fingerprint, _ in sorted(entries, key=lambda item: (item[0], item[1])):
        digest.update(f'{actual}:{fingerprint}\n'.encode())
    for actual, _, path in entries:
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert('RGB').resize((224, 224))
            value = np.asarray(image, dtype='float32')[None, ...]
        score = float(model(value, training=False).numpy().reshape(-1)[0])
        if not np.isfinite(score) or not 0 <= score <= 1:
            raise ValueError('Invalid model score')
        matrix[actual][int(score >= .75)] += 1
    (tn, fp), (fn, tp) = matrix
    def class_metrics(correct, false_positive, false_negative):
        precision = correct / (correct + false_positive) if correct + false_positive else 0
        recall = correct / (correct + false_negative) if correct + false_negative else 0
        return {'precision': precision, 'recall': recall,
                'f1': 2 * precision * recall / (precision + recall) if precision + recall else 0}
    return {'matrix_order': CLASSES, 'confusion_matrix': matrix, 'n': len(entries),
            'accuracy': (tn + tp) / len(entries), 'high_potential_precision': tp / (tp + fp) if tp + fp else 0,
            'high_potential_recall': tp / (tp + fn) if tp + fn else 0,
            'high_potential_f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0,
            'per_class': {'Normal': class_metrics(tn, fn, fp), 'High Potential': class_metrics(tp, fp, fn)},
            'dataset_sha256': digest.hexdigest()}


def training_graph(name, history, out):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, metric in zip(axes, ['accuracy', 'loss']):
        ax.plot(range(1, len(history[metric]) + 1), history[metric], label='Training')
        ax.plot(range(1, len(history['val_' + metric]) + 1), history['val_' + metric], label='Validation')
        ax.set(title=name + (' accuracy (0.50 threshold)' if metric == 'accuracy' else ' loss'), xlabel='Epoch', ylabel=metric.title())
        ax.legend()
        ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(out / (name + '_training_accuracy_loss.png'), dpi=180)
    plt.close(fig)


def confusion_graph(name, matrix, out, split='test'):
    fig, ax = plt.subplots(figsize=(5, 4))
    grid = np.asarray(matrix)
    ax.imshow(grid, cmap='Blues')
    ax.set(title=name + ' ' + split + ' confusion matrix (0.75)', xlabel='Predicted', ylabel='Actual',
           xticks=[0, 1], yticks=[0, 1], xticklabels=['Normal', 'High Potential'], yticklabels=['Normal', 'High Potential'])
    for row in range(2):
        for col in range(2):
            ax.text(col, row, str(grid[row, col]), ha='center', va='center', color='white' if grid[row, col] > grid.max() / 2 else 'black')
    fig.tight_layout()
    fig.savefig(out / (name + '_confusion_matrix.png'), dpi=180)
    plt.close(fig)


def comparison_graphs(results, out):
    models = results['models']
    names = list(models)
    if not names:
        return
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(names, [models[name]['evaluation']['accuracy'] * 100 for name in names])
    ax.set(title='Test accuracy at 0.75 threshold', ylabel='Accuracy (%)', ylim=(0, 100))
    fig.tight_layout()
    fig.savefig(out / 'model_test_accuracy_comparison.png', dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 4))
    metrics = ['accuracy', 'high_potential_precision', 'high_potential_recall', 'high_potential_f1']
    labels = ['Accuracy', 'High Potential precision', 'High Potential recall', 'High Potential F1']
    x = np.arange(len(names))
    for i, (metric, label) in enumerate(zip(metrics, labels)):
        ax.bar(x + (i - 1.5) * .19, [models[name]['evaluation'][metric] * 100 for name in names], .19, label=label)
    ax.set(title='Test performance at 0.75 threshold', ylabel='Percent', ylim=(0, 100), xticks=x, xticklabels=names)
    ax.legend(fontsize=8, loc='upper center', bbox_to_anchor=(.5, -.16), ncol=2)
    fig.tight_layout()
    fig.savefig(out / 'model_test_performance_comparison.png', dpi=180)
    plt.close(fig)
    import csv
    with (out / 'model_classification_results.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['Model', 'Test accuracy', 'Class', 'Precision', 'Recall', 'F1', 'Threshold'])
        for name in names:
            evaluation = models[name]['evaluation']
            for label, metrics in evaluation['per_class'].items():
                writer.writerow([name, evaluation['accuracy'], label, metrics['precision'], metrics['recall'], metrics['f1'], .75])


def main():
    out = OUT_ROOT / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out.mkdir(parents=True, exist_ok=False)
    print('Experiment output:', out, flush=True)
    print('Test set was used in previous work; results are not independent validation.', flush=True)
    results = {'classes': CLASSES, 'threshold': .75, 'seed': SEED, 'epochs_max': 5,
               'note': 'Existing image-level split and previously used test set; writer independence unverified.',
               'tensorflow': tf.__version__, 'models': {}}
    for name in ('MobileNetV2', 'EfficientNetB0', 'ResNet50'):
        tf.keras.utils.set_random_seed(SEED)
        print('Training', name, flush=True)
        model = build(name)
        history = model.fit(dataset('train', True), validation_data=dataset('validation'), epochs=5,
                            callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=2,
                                                                       restore_best_weights=True)], verbose=2)
        target = out / (name + '.keras')
        model.save(target)
        results['models'][name] = {'epochs': len(history.history['loss']), 'history': history.history,
                                   'evaluation': evaluate(model), 'artifact_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
        (out / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
        training_graph(name, history.history, out)
        confusion_graph(name, results['models'][name]['evaluation']['confusion_matrix'], out)
        comparison_graphs(results, out)
        print('Completed', name, json.dumps(results['models'][name]['evaluation']), flush=True)
        del model
        tf.keras.backend.clear_session()
    print('Experiment complete; no app model or catalogue was updated.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Experiment stopped:', type(error).__name__, str(error), file=sys.stderr, flush=True)
        raise
