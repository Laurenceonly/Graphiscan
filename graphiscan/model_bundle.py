"""Private build-time model transport; bounded, content-addressed chunks only."""
import hashlib
import json
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory

CHUNK_BYTES = 32*1024*1024
MAX_BUNDLE_BYTES = 160*1024*1024
MANIFEST = 'model/deployment.litert.local.json'
ARTIFACT = re.compile(r'model/versions/(mobilenetv2|efficientnetb0|resnet50)-([a-f0-9]{64})\.tflite')


def validate_descriptor(document):
    if set(document) != {'schema_version', 'files'} or document['schema_version'] != 1:
        raise ValueError('Unsupported model bundle')
    files = document['files']
    if not isinstance(files, list) or len(files) != 4:
        raise ValueError('Require one manifest and three model files')
    paths, architectures, total = set(), set(), 0
    for item in files:
        if set(item) != {'path', 'sha256', 'size', 'parts'}:
            raise ValueError('Invalid model file descriptor')
        path, digest, size = item['path'], item['sha256'], item['size']
        if not isinstance(path, str) or path in paths:
            raise ValueError('Invalid duplicate model path')
        match = ARTIFACT.fullmatch(path)
        if path != MANIFEST and not match:
            raise ValueError('Unapproved model destination')
        if not isinstance(digest, str) or re.fullmatch('[a-f0-9]{64}', digest) is None:
            raise ValueError('Invalid file digest')
        if type(size) is not int or not 0 < size <= (65536 if path == MANIFEST else 128*1024*1024):
            raise ValueError('Invalid model file size')
        if match:
            if digest != match[2] or match[1] in architectures:
                raise ValueError('Model path/digest conflict')
            architectures.add(match[1])
        parts = item['parts']
        if not isinstance(parts, list) or not 1 <= len(parts) <= 4:
            raise ValueError('Invalid model chunks')
        for part in parts:
            if set(part) != {'sha256', 'size'} or not isinstance(part['sha256'], str) or re.fullmatch('[a-f0-9]{64}', part['sha256']) is None:
                raise ValueError('Invalid chunk identity')
            if type(part['size']) is not int or not 0 < part['size'] <= CHUNK_BYTES:
                raise ValueError('Invalid chunk size')
        if sum(part['size'] for part in parts) != size:
            raise ValueError('Chunk sizes do not match the file')
        paths.add(path)
        total += size
    if MANIFEST not in paths or architectures != {'mobilenetv2', 'efficientnetb0', 'resnet50'} or total > MAX_BUNDLE_BYTES:
        raise ValueError('Incomplete or oversized model bundle')
    return files


def prepare_bundle(root, destination):
    """Local preparation only: do not load configuration or make network calls."""
    from v1_lite_models import LiteBinaryRuntime
    from v1_uploads import file_digest
    runtime = LiteBinaryRuntime(root / MANIFEST)
    destination.mkdir(parents=True, exist_ok=True)
    parts_dir = destination / 'parts'
    parts_dir.mkdir(exist_ok=True)
    sources = [root / MANIFEST] + [value[1] for _, value in sorted(runtime.entries.items())]
    document = {'schema_version': 1, 'files': []}
    for source in sources:
        item = {'path': source.relative_to(root).as_posix(), 'sha256': file_digest(source),
                'size': source.stat().st_size, 'parts': []}
        with source.open('rb') as stream:
            while block := stream.read(CHUNK_BYTES):
                digest = hashlib.sha256(block).hexdigest()
                target = parts_dir / digest
                if target.exists():
                    if file_digest(target) != digest:
                        raise ValueError('Existing private chunk changed')
                else:
                    target.write_bytes(block)
                item['parts'].append({'sha256': digest, 'size': len(block)})
        document['files'].append(item)
    validate_descriptor(document)
    (destination / 'descriptor.json').write_text(json.dumps(document, indent=2)+'\n', encoding='utf-8')
    return document


def fetch_bundle(document, client, bucket, root):
    """Download verified chunks; install the manifest last, before server startup."""
    from v1_uploads import file_digest
    files = validate_descriptor(document)
    if not isinstance(bucket, str) or re.fullmatch('[a-z0-9][a-z0-9_-]{0,62}', bucket) is None:
        raise ValueError('Invalid private artifact bucket')
    root = root.resolve()
    if not (root / 'model').resolve().is_relative_to(root):
        raise ValueError('Model directory escapes application')
    (root / 'model').mkdir(exist_ok=True)
    with TemporaryDirectory(prefix='model-bundle-', dir=root / 'model') as folder:
        staged = []
        for index, item in enumerate(files):
            target = (root / item['path']).resolve()
            if not target.is_relative_to(root):
                raise ValueError('Model destination escapes application')
            if target.exists() and file_digest(target) == item['sha256']:
                continue
            if target.exists() and item['path'] != MANIFEST:
                raise ValueError('Existing immutable artifact changed')
            temporary = Path(folder) / str(index)
            overall = hashlib.sha256()
            with temporary.open('wb') as output:
                for part in item['parts']:
                    response = client.get_object(Bucket=bucket, Key='sha256/'+part['sha256'])
                    stream = response['Body']
                    checksum, received = hashlib.sha256(), 0
                    try:
                        if response.get('ContentLength') != part['size']:
                            raise ValueError('Private chunk size mismatch')
                        while block := stream.read(min(1024*1024, part['size']-received+1)):
                            received += len(block)
                            if received > part['size']:
                                raise ValueError('Private chunk exceeds limit')
                            checksum.update(block)
                            overall.update(block)
                            output.write(block)
                    finally:
                        stream.close()
                    if received != part['size'] or checksum.hexdigest() != part['sha256']:
                        raise ValueError('Private chunk identity mismatch')
            if temporary.stat().st_size != item['size'] or overall.hexdigest() != item['sha256']:
                raise ValueError('Private model identity mismatch')
            staged.append((item['path'], temporary, target))
        # No destination is changed until every fetched file is verified.
        for _, temporary, target in sorted(staged, key=lambda item: item[0] == MANIFEST):
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(temporary, target)
    return root / MANIFEST
