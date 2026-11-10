"""Fine-tune copies of the existing EfficientNetB0 and ResNet50 on validation only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import train_binary_experiment as base

tf = base.tf


def run(name):
    output = base.OUT_ROOT / ('finetune-' + name + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    output.mkdir(parents=True, exist_ok=False)
    source = base.ROOT / 'training_results/models' / (name + '_best.keras')
    tf.keras.utils.set_random_seed(base.SEED)
    model = tf.keras.models.load_model(source, compile=False, safe_mode=False,
        custom_objects={'preprocess_input': tf.keras.applications.resnet50.preprocess_input})
    candidates = [layer for layer in model.layers if isinstance(layer, tf.keras.Model) and layer is not model and not layer.trainable]
    if len(candidates) != 1:
        raise ValueError('Expected exactly one frozen pretrained backbone')
    backbone = candidates[0]
    print('Fine-tuning output:', output, flush=True)
    print('Measuring existing', name, 'on validation at 0.75.', flush=True)
    before = base.evaluate(model, split='validation')
    backbone.trainable = True
    for layer in backbone.layers[:-20]:
        layer.trainable = False
    for layer in backbone.layers[-20:]:
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-5), loss='binary_crossentropy',
                  metrics=[tf.keras.metrics.BinaryAccuracy(name='accuracy', threshold=.75)])
    print('Training up to three epochs; batch normalization remains frozen.', flush=True)
    history = model.fit(base.dataset('train', True), validation_data=base.dataset('validation'), epochs=3,
                        callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=2, restore_best_weights=True)], verbose=2)
    target = output / (name + '_finetuned.keras')
    model.save(target)
    print('Measuring fine-tuned model on validation at 0.75.', flush=True)
    after = base.evaluate(model, split='validation')
    results = {'model': name, 'source_model_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
               'artifact_sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'seed': base.SEED,
               'learning_rate': 1e-5, 'epochs_run': len(history.history['loss']), 'threshold': .75,
               'validation_before': before, 'validation_after': after, 'history': history.history,
               'test_set_used': False, 'limitation': 'Existing validation split reused; writer independence unverified.'}
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
    parser = argparse.ArgumentParser()
    parser.add_argument('model', choices=['EfficientNetB0', 'ResNet50'])
    run(parser.parse_args().model)
