#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json

EVIDENCE = Path('/root/projects/GPU加速/evidence/session/gate-a-a1')
RUN_ID = '34688831275'
ROOT = EVIDENCE / 'artifacts' / RUN_ID
METADATA = json.loads((EVIDENCE / 'ci-artifacts.json').read_text())
SELECTED = {
    'termux-x11-universal-debug': 'termux-x11-universal-debug.apk',
    'termux-x11-unstripped-libraries-for-ndk-stack': '01x55434',
}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def file_record(path):
    return {
        'path': str(path),
        'bytes': path.stat().st_size,
        'sha256': digest(path),
    }

records = {}
for artifact in METADATA['artifacts']:
    name = artifact['name']
    if name not in SELECTED:
        continue
    assert not artifact['expired'], artifact
    assert artifact['size_in_bytes'] > 0, artifact
    if name.endswith('universal-debug'):
        path = ROOT / SELECTED[name]
        assert path.is_file(), path
        records[name] = {
            'metadata': artifact,
            'downloaded_files': [file_record(path)],
        }
    else:
        directory = ROOT / SELECTED[name]
        assert directory.is_dir(), directory
        files = [file_record(path) for path in sorted(directory.rglob('*')) if path.is_file()]
        assert files, directory
        records[name] = {
            'metadata': artifact,
            'downloaded_files': files,
            'downloaded_file_count': len(files),
            'downloaded_total_bytes': sum(item['bytes'] for item in files),
        }
assert set(records) == set(SELECTED), records

manifest = {
    'repo': 'waydefu/termux-x11',
    'run_id': RUN_ID,
    'download_root': str(ROOT),
    'selected_by_exact_artifact_name': list(SELECTED),
    'selected_artifacts': records,
}
(EVIDENCE / 'artifact-download-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
