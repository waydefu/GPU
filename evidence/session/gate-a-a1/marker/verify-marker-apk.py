#!/usr/bin/env python3
"""Gate A A1 marker-iteration APK/ELF verifier (run 34694695463, HEAD 4196798)."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import zipfile

MARKER = Path('/root/projects/GPU加速/evidence/session/gate-a-a1/marker')
ART = MARKER / 'artifacts-34694695463'
APK = ART / 'universal' / 'termux-x11-universal-debug.apk'
OUT = MARKER / 'apk-elf-verification'
OUT.mkdir(parents=True, exist_ok=True)
LIB_REL = 'lib/arm64-v8a/libXlorie.so'
EXPECTED_SIGNER = 'b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1'
SDK_BT = '/root/android-sdk/build-tools/36.0.0'
APKANALYZER = '/root/android-sdk/cmdline-tools/latest/bin/apkanalyzer'


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def run_capture(label, args):
    try:
        result = subprocess.run(args, capture_output=True, check=False)
        rc, out, err = result.returncode, result.stdout, result.stderr
    except OSError as error:
        rc, out, err = 127, b'', f'{type(error).__name__}: {error}'.encode()
    (OUT / f'{label}.stdout.txt').write_bytes(out)
    (OUT / f'{label}.stderr.txt').write_bytes(err)
    (OUT / f'{label}.status').write_text(
        json.dumps({'argv': args, 'returncode': rc}, indent=2) + '\n')
    return rc, out.decode(errors='replace'), err.decode(errors='replace')


assert APK.is_file() and APK.stat().st_size > 0, APK
report = {'apk_path': str(APK), 'apk_bytes': APK.stat().st_size,
          'apk_sha256': sha256(APK)}

with zipfile.ZipFile(APK) as zf:
    infos = zf.infolist()
    names = [i.filename for i in infos]
    report['testzip'] = zf.testzip()
    report['member_count'] = len(infos)
    report['duplicate_names'] = sorted({n for n in names if names.count(n) > 1})
    report['arm64_member_present'] = LIB_REL in names
    stored = [i for i in infos if i.compress_type == zipfile.ZIP_STORED]
    bad = 0
    with open(APK, 'rb') as f:
        for i in stored:
            f.seek(i.header_offset)
            local = f.read(30)
            if len(local) < 30:
                bad += 1
                continue
            name_len, extra_len = int.from_bytes(local[26:28], 'little'), int.from_bytes(local[28:30], 'little')
            if (i.header_offset + 30 + name_len + extra_len) % 4 != 0:
                bad += 1
    report['stored_count'] = len(stored)
    report['stored_mod4_failures'] = bad

with zipfile.ZipFile(APK) as zf:
    embedded = OUT / 'libXlorie-embedded.so'
    embedded.write_bytes(zf.read(LIB_REL))
report['embedded_sha256'] = sha256(embedded)

unstripped = sorted(ART.glob('unstripped/**/obj/arm64-v8a/libXlorie.so'))
assert len(unstripped) == 1, unstripped
unstripped = unstripped[0]
report['unstripped_path'] = str(unstripped)
report['unstripped_sha256'] = sha256(unstripped)

build_ids = {}
for label, path in (('embedded', embedded), ('unstripped', unstripped)):
    rc, out, _ = run_capture(f'{label}-readelf-n', ['readelf', '-n', str(path)])
    assert rc == 0, label
    match = re.search(r'Build ID:\s*([0-9a-f]+)', out)
    assert match, label
    build_ids[label] = match.group(1)
report['build_ids'] = build_ids
report['build_id_equal'] = build_ids['embedded'] == build_ids['unstripped']

markers = {}
for label, path in (('embedded', embedded), ('unstripped', unstripped)):
    rc, out, _ = run_capture(f'{label}-strings-marker', ['strings', '-a', str(path)])
    assert rc == 0, label
    markers[label] = {key: (key in out) for key in (
        'GATEA_A1_PRECALL', 'GATEA_A1_ENTRY', 'gateaA1MicroprobeRun', 'GATEA_A1')}
report['marker_strings'] = markers

manifest = {}
for label, sub in (('application-id', 'application-id'), ('version-code', 'version-code'),
                   ('version-name', 'version-name')):
    rc, out, _ = run_capture(f'manifest-{label}', [APKANALYZER, 'manifest', sub, str(APK)])
    manifest[label] = {'returncode': rc, 'value': out.strip()}
report['manifest'] = manifest

rc, out, _ = run_capture('apksigner-verify', [f'{SDK_BT}/apksigner', 'verify',
                                              '--verbose', '--print-certs', str(APK)])
report['apksigner_returncode'] = rc
certs = re.findall(r'SHA-256 digest:\s*([0-9a-fA-F]+)', out)
report['signer_sha256_list'] = [c.lower() for c in certs]
report['signer_exact_match_p2b2'] = EXPECTED_SIGNER in report['signer_sha256_list']

(OUT / 'marker-apk-elf-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
