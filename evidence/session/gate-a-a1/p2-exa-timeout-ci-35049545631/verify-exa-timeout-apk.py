#!/usr/bin/env python3
"""Qualify the EXA Composite timeout-repair CI APK (run 35049545631)."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import zipfile

EVID = Path('/root/projects/GPU加速/evidence/session/gate-a-a1/p2-exa-timeout-ci-35049545631')
APK = EVID / 'apk' / 'termux-x11-universal-debug.apk'
OUT = EVID / 'apk-elf-verification'
OUT.mkdir(parents=True, exist_ok=True)
LIB_REL = 'lib/arm64-v8a/libXlorie.so'
EXPECTED_SIGNER = 'b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1'
EXPECTED_PKG = 'com.waydefu.x11gpu'
EXPECTED_HEAD = '0d72332c0e591b2137262d06d7dcab704be49383'
EXPECTED_HEAD_SHORT = '0d72332'
CI_RUN = 35049545631
PREVIOUS_APK_SHA256 = 'c29b1c68df613d40d8bfd93b44887ffd389419d8ca5f36661d1a48b3f03f4c2c'
AAPT = '/usr/bin/aapt'
APKSIGNER = '/usr/bin/apksigner'
EXPECTED_ABIS = (
    'lib/arm64-v8a/libXlorie.so',
    'lib/armeabi-v7a/libXlorie.so',
    'lib/x86/libXlorie.so',
    'lib/x86_64/libXlorie.so',
)

REQUIRED_STRINGS = (
    'x-exa-composite-wait',
    'EXA GPU composite wait timeout',
    'TERMUX_X11_GATEA_TEST_FAULT',
    'TERMUX_X11_GATEA_TEST_ARM',
    'x-test-fault-env',
    'GATEA_SUMMARY',
    'r-test-fatal-pre-fence',
    'x-present-copy-wait',
    'TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL',
    'GATEA_FATAL_HALT',
)
# Static helper name is stripped from the embedded .so; prove it via unstripped nm.
FORBIDDEN_STRINGS = (
    'direct-to-legacy',
    'CPU fallback as PASS',
)
NM_REQUIRED = (
    'present_gpu_copy_retire_or_fatal',
    'lorieGateADumpSummary',
    'lorieGateATracePresentRetire',
    'lorieGateACopyBufferId',
    'lorieGpuCopyWaitForPresentOrFatal',
    'lorieGateATraceXRequest',
)
# Composite helper is static and inlined; prove it via unstripped strings, not nm.


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
report = {
    'apk_path': str(APK),
    'apk_bytes': APK.stat().st_size,
    'apk_sha256': sha256(APK),
    'head': EXPECTED_HEAD,
    'ci_run': CI_RUN,
}
assert report['apk_sha256'] != PREVIOUS_APK_SHA256, 'downloaded previous a7528bd APK'
run_meta = json.loads((EVID / 'run.json').read_text())
assert run_meta['headSha'] == EXPECTED_HEAD, run_meta
assert run_meta['conclusion'] == 'success', run_meta
assert run_meta['event'] == 'workflow_dispatch', run_meta
assert run_meta['databaseId'] == CI_RUN, run_meta
report['ci'] = run_meta

with zipfile.ZipFile(APK) as zf:
    infos = zf.infolist()
    names = [i.filename for i in infos]
    report['testzip'] = zf.testzip()
    report['member_count'] = len(infos)
    report['libxlories'] = sorted(n for n in names if n.endswith('libXlorie.so'))
    stored = [i for i in infos if i.compress_type == zipfile.ZIP_STORED]
    bad = 0
    with open(APK, 'rb') as handle:
        for info in stored:
            handle.seek(info.header_offset)
            local = handle.read(30)
            if len(local) < 30:
                bad += 1
                continue
            name_len = int.from_bytes(local[26:28], 'little')
            extra_len = int.from_bytes(local[28:30], 'little')
            if (info.header_offset + 30 + name_len + extra_len) % 4 != 0:
                bad += 1
    report['stored_count'] = len(stored)
    report['stored_mod4_failures'] = bad
    embedded = OUT / 'libXlorie-embedded.so'
    embedded.write_bytes(zf.read(LIB_REL))

assert report['testzip'] is None
assert report['libxlories'] == list(EXPECTED_ABIS), report['libxlories']
assert report['stored_mod4_failures'] == 0
report['embedded_sha256'] = sha256(embedded)
report['abis'] = report['libxlories']

unstripped = sorted((EVID / 'unstripped').glob('**/obj/arm64-v8a/libXlorie.so'))
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
assert report['build_id_equal'], build_ids

strings = {}
for label, path in (('embedded', embedded), ('unstripped', unstripped)):
    rc, out, _ = run_capture(f'{label}-strings', ['strings', '-a', str(path)])
    assert rc == 0, label
    present = {key: (key in out) for key in REQUIRED_STRINGS}
    absent = {key: (key not in out) for key in FORBIDDEN_STRINGS}
    helper_name = 'lorieGpuCopyWaitForCompositeOrFatal' in out
    strings[label] = {
        'required': present,
        'forbidden_absent': absent,
        'helper_name': helper_name,
    }
    assert all(present.values()), (label, present)
    assert all(absent.values()), (label, absent)
    if label == 'unstripped':
        assert helper_name, 'unstripped missing helper name string'
report['strings'] = strings

rc, out, _ = run_capture('unstripped-nm', ['nm', '-a', '-C', str(unstripped)])
assert rc == 0
nm_found = {sym: (sym in out) for sym in NM_REQUIRED}
report['nm'] = nm_found
assert all(nm_found.values()), nm_found
report['nm_composite_helper_inlined'] = 'lorieGpuCopyWaitForCompositeOrFatal' not in out
assert report['nm_composite_helper_inlined']
assert strings['unstripped']['helper_name']
assert strings['embedded']['required']['x-exa-composite-wait']
assert strings['embedded']['required']['EXA GPU composite wait timeout']
report['test_env_default_off'] = (
    'setenv("TERMUX_X11_GATEA_TEST_FAULT"' not in Path(
        '/root/projects/GPU加速/src/f8-ahb-gatea-exa-timeout/lorie/src/main/cpp/lorie/InitOutput.c'
    ).read_text()
)
assert report['test_env_default_off']

rc, out, _ = run_capture('aapt-dump', [AAPT, 'dump', 'badging', str(APK)])
assert rc == 0, out
pkg = re.search(r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", out)
assert pkg, out[:500]
report['aapt_rc'] = rc
report['package'] = pkg.group(1)
report['versionCode'] = pkg.group(2)
report['versionName'] = pkg.group(3)
assert report['package'] == EXPECTED_PKG
assert EXPECTED_HEAD_SHORT in report['versionName'], report['versionName']
assert 'com.termux.x11' != report['package']

rc, out, _ = run_capture('apksigner', [APKSIGNER, 'verify', '--verbose', '--print-certs', str(APK)])
certs = [c.lower() for c in re.findall(r'SHA-256 digest:\s*([0-9a-fA-F]+)', out)]
report['apksigner_rc'] = rc
report['signer_sha256'] = certs[0] if certs else None
assert rc == 0 and EXPECTED_SIGNER in certs, certs

(OUT / 'p2-exa-timeout-apk-elf-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({
    'apk_sha256': report['apk_sha256'],
    'apk_bytes': report['apk_bytes'],
    'package': report['package'],
    'versionCode': report['versionCode'],
    'versionName': report['versionName'],
    'abis': report['abis'],
    'signer': report['signer_sha256'],
    'build_ids': report['build_ids'],
    'build_id_equal': report['build_id_equal'],
    'repair_strings': strings['embedded']['required'],
    'nm': report['nm'],
    'test_env_default_off': report['test_env_default_off'],
}, indent=2))
