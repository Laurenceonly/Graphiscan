"""Fine-tune a copy of the existing MobileNetV2; assess on validation only."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import train_binary_experiment as base

tf = base.tf
ROOT = base.ROOT


def main():
    output = base.OUT_ROOT / ('finetune-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    output.mkdir(parents=True, exist_ok=False)
    source = ROOT / 'training_results/models/MobileNetV2_best.keras'
    tf.keras.utils.set_random_seed(base.SEED)
    model = tf.keras.models.load_model(source, compile=False, safe_mode=False)
    backbone = next(layer for layer in model.layers if layer.name.startswith('mobilenetv2_') and isinstance(layer, tf.keras.Model))
    if backbone.trainable:
        raise ValueError('Expected existing frozen MobileNetV2 backbone')
    print('Fine-tuning output:', output, flush=True)
    print('Measuring existing model on validation set at 0.75.', flush=True)
    before = base.evaluate(model, split='validation')
    backbone.trainable = True
    for layer in backbone.layers[:-20]:
        layer.trainable = False
    for layer in backbone.layers[-20:]:
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-5), loss='binary_crossentropy',
                  metrics=[tf.keras.metrics.BinaryAccuracy(name='accuracy', threshold=.75)])
    print('Training up to three epochs; batch-normalization layers remain frozen.', flush=True)
    history = model.fit(base.dataset('train', True), validation_data=base.dataset('validation'), epochs=3,
                        callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=2, restore_best_weights=True)], verbose=2)
    target = output / 'MobileNetV2_finetuned.keras'
    model.save(target)
    print('Measuring fine-tuned model on validation set at 0.75.', flush=True)
    after = base.evaluate(model, split='validation')
    results = {'source_model_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
               'artifact_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
               'seed': base.SEED, 'learning_rate': 1e-5, 'epochs_run': len(history.history['loss']),
               'threshold': .75, 'validation_before': before, 'validation_after': after,
               'history': history.history, 'test_set_used': False,
               'limitation': 'Existing validation split is reused; writer independence unverified.'}
    (output / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    fig, axes = base.plt.subplots(1, 2, figsize=(10, 4))
    for axis, metric in zip(axes, ['accuracy', 'loss']):
        axis.plot(range(1, len(history.history[metric])+1), history.history[metric], label='Training')
        axis.plot(range(1, len(history.history['val_'+metric])+1), history.history['val_'+metric], label='Validation')
        axis.set(title='Accuracy (0.75 threshold)' if metric=='accuracy' else 'Loss', xlabel='Epoch', ylabel=metric.title())
        axis.legend(); axis.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(output / 'finetuning_accuracy_loss.png', dpi=180); base.plt.close(fig)
    base.confusion_graph('Before fine-tuning', before['confusion_matrix'], output, split='validation')
    base.confusion_graph('After fine-tuning', after['confusion_matrix'], output, split='validation')
    print('Validation before:', json.dumps(before), flush=True)
    print('Validation after:', json.dumps(after), flush=True)
    print('Complete. Test set and app models were not changed.', flush=True)


if __name__ == '__main__':
    main()
