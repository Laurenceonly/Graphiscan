"""Measure the pinned runtime with a generated image; no database or student data."""
import argparse
import ctypes
from io import BytesIO
import json
import os
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def memory_mib():
    if sys.platform == 'win32':
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in (
                    'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
                    'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
                    'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage', 'PrivateUsage')]

        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        process = ctypes.windll.kernel32.GetCurrentProcess
        process.restype = wintypes.HANDLE
        measure = ctypes.windll.psapi.GetProcessMemoryInfo
        measure.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        if not measure(process(), ctypes.byref(counters), counters.cb):
            raise OSError('Process memory measurement unavailable')
        return {'resident_mib': round(counters.WorkingSetSize / 2**20, 2),
                'peak_resident_mib': round(counters.PeakWorkingSetSize / 2**20, 2),
                'private_mib': round(counters.PrivateUsage / 2**20, 2)}
    import resource
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result = {'peak_resident_mib': round(peak / (2**20 if sys.platform == 'darwin' else 1024), 2)}
    if sys.platform.startswith('linux'):
        pages = int(Path('/proc/self/statm').read_text().split()[1])
        result['resident_mib'] = round(pages * os.sysconf('SC_PAGE_SIZE') / 2**20, 2)
        # In the Linux container, include the enforced cgroup and its whole-
        # container peak (including charged page cache), not only process RSS.
        cgroup = Path('/sys/fs/cgroup')
        for filename, field in [('memory.max', 'cgroup_limit_bytes'),
                                ('memory.current', 'cgroup_current_bytes'),
                                ('memory.peak', 'cgroup_peak_bytes')]:
            path = cgroup / filename
            if path.is_file():
                value = path.read_text().strip()
                result[field] = int(value) if value.isdigit() else value
        events = cgroup / 'memory.events'
        if events.is_file():
            result['cgroup_events'] = {key: int(value) for key, value in
                                       (line.split() for line in events.read_text().splitlines())}
    return result


def profile(manifest, selected):
    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
    os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')
    os.environ.setdefault('TF_NUM_INTRAOP_THREADS', '2')
    os.environ.setdefault('TF_NUM_INTEROP_THREADS', '1')
    from PIL import Image, ImageDraw
    from v1_models import VersionedBinaryRuntime
    from v1_uploads import normalize_image

    runtime = VersionedBinaryRuntime(manifest)
    keys = selected or sorted(runtime.entries, key=lambda key: (key != 'mobilenetv2', key))
    if any(key not in runtime.entries for key in keys):
        raise ValueError('Requested model is not installed')
    image = Image.new('RGB', (224, 224), 'white')
    draw = ImageDraw.Draw(image)
    for y in (64, 112, 160):
        draw.line([(32, y), (64, y-15), (96, y+10), (128, y-10), (176, y)], fill='black', width=3)
    source = BytesIO()
    image.save(source, format='PNG')
    source.seek(0)
    sample = normalize_image(source)
    report = {'status': 'profiling', 'platform': platform.system(),
              'python_version': platform.python_version(), 'sample': 'generated-lines-only',
              'baseline': memory_mib(), 'models': [], 'database_accessed': False,
              'artifacts_changed': False, 'limitations': [
                  'Synthetic timing/memory measurement, not an accuracy evaluation.',
                  'Local OS/process metrics do not establish Linux container memory limits.',
                  'No Auth/database/Storage, network latency or concurrent-upload overhead measured.']}
    for key in keys:
        entry, artifact = runtime.entries[key]
        model = {**entry, 'task_type': 'binary', 'provenance': 'verified'}
        started = time.perf_counter()
        runtime.infer(sample, model)
        cold = time.perf_counter() - started
        started = time.perf_counter()
        runtime.infer(sample, model)
        item = {'model_key': key, 'artifact_mib': round(artifact.stat().st_size / 2**20, 2),
                'first_inference_seconds': round(cold, 3),
                'warm_inference_seconds': round(time.perf_counter() - started, 3),
                'cached_model_count': len(runtime.networks), 'memory': memory_mib()}
        report['models'].append(item)
        print(json.dumps({'status': 'model-profiled', **item}), flush=True)
    report['status'] = 'profile-complete'
    report['final_memory'] = memory_mib()
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'model/deployment.local.json')
    parser.add_argument('--model', action='append', choices=['mobilenetv2', 'efficientnetb0', 'resnet50'])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        report = profile(args.manifest, args.model)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report), flush=True)
    except Exception:
        print(json.dumps({'status': 'profile-not-confirmed', 'private_error_omitted': True}), flush=True)
        sys.exit(1)
