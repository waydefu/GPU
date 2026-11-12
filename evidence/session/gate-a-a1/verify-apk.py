#!/usr/bin/env python3
from collections import Counter
from pathlib import Path
import hashlib
import json
import re
import shutil
import struct
import subprocess
import zipfile
from types import SimpleNamespace

EVIDENCE = Path('/root/projects/GPU加速/evidence/session/gate-a-a1')
RUN_ID = '34688831275'
APK = EVIDENCE / 'artifacts' / RUN_ID / 'termux-x11-universal-debug.apk'
OUT = EVIDENCE / 'apk-verification'
LIB_REL = 'lib/arm64-v8a/libXlorie.so'
OUT.mkdir(parents=True, exist_ok=True)

def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def run_capture(label, args):
    try:
        result = subprocess.run(args, capture_output=True, check=False)
    except OSError as error:
        result = SimpleNamespace(
            returncode=127,
            stdout=b'',
            stderr=f'{type(error).__name__}: {error}'.encode(),
        )
    (OUT / f'{label}.stdout.txt').write_bytes(result.stdout)
    (OUT / f'{label}.stderr.txt').write_bytes(result.stderr)
    (OUT / f'{label}.status').write_text(
        json.dumps({'argv': args, 'returncode': result.returncode}, indent=2) + '\n')
    return result

def tool(name, candidates):
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return str(path)
    return shutil.which(name)

assert APK.is_file(), APK
assert APK.stat().st_size > 0

zip_report = {
    'path': str(APK),
    'bytes': APK.stat().st_size,
    'sha256': sha256(APK),
    'bad_member': None,
    'duplicate_names': [],
    'member_count': 0,
    'arm64_member': LIB_REL in (),
    'stored_data_offsets_mod4': {},
    'stored_misaligned_members': [],
}
with zipfile.ZipFile(APK, 'r') as archive:
    infos = archive.infolist()
    names = [info.filename for info in infos]
    zip_report['member_count'] = len(names)
    zip_report['duplicate_names'] = sorted(name for name, count in Counter(names).items() if count > 1)
    zip_report['bad_member'] = archive.testzip()
    zip_report['arm64_member'] = LIB_REL in names
    for info in infos:
        if info.compress_type != zipfile.ZIP_STORED:
            continue
        archive.fp.seek(info.header_offset)
        header = archive.fp.read(30)
        signature, _version, _flags, _method, _mtime, _mdate, _crc, _csize, _usize, name_len, extra_len = struct.unpack('<4s5H3I2H', header)
        assert signature == b'PK\x03\x04', (info.filename, signature)
        data_offset = info.header_offset + 30 + name_len + extra_len
        zip_report['stored_data_offsets_mod4'][info.filename] = data_offset % 4
        if data_offset % 4:
            zip_report['stored_misaligned_members'].append(info.filename)
    assert zip_report['bad_member'] is None, zip_report
    assert not zip_report['duplicate_names'], zip_report
    assert zip_report['arm64_member'], zip_report
    member = archive.getinfo(LIB_REL)
    extracted = OUT / 'libXlorie-embedded.so'
    extracted.write_bytes(archive.read(member))
zip_report['embedded_library_path'] = str(OUT / 'libXlorie-embedded.so')
zip_report['embedded_library_bytes'] = (OUT / 'libXlorie-embedded.so').stat().st_size
zip_report['embedded_library_sha256'] = sha256(OUT / 'libXlorie-embedded.so')
(OUT / 'apk-zip-report.json').write_text(json.dumps(zip_report, indent=2) + '\n')

# Capture the Android tooling results independently. Java-backed tools may run on ARM64;
# native x86-64 build-tools are retained as explicit host-tool results.
aapt2 = '/root/android-sdk/build-tools/36.0.0/aapt2'
apksigner = '/root/android-sdk/build-tools/36.0.0/apksigner'
zipalign = '/root/android-sdk/build-tools/36.0.0/zipalign'
apkanalyzer = tool('apkanalyzer', [
    '/root/android-sdk/cmdline-tools/latest/bin/apkanalyzer',
])
run_capture('host-uname', ['uname', '-m'])
run_capture('aapt2-file', ['file', aapt2])
run_capture('aapt2-badging', [aapt2, 'dump', 'badging', str(APK)])
run_capture('apksigner-version', [apksigner, 'version'])
run_capture('apksigner-verify', [apksigner, 'verify', '--verbose', '--print-certs', str(APK)])
run_capture('zipalign-file', ['file', zipalign])
run_capture('zipalign-check', [zipalign, '-c', '-v', '4', str(APK)])
run_capture('apkanalyzer-file', ['file', apkanalyzer] if apkanalyzer else ['true'])
if apkanalyzer:
    run_capture('apkanalyzer-application-id', [apkanalyzer, 'manifest', 'application-id', str(APK)])
    run_capture('apkanalyzer-version-code', [apkanalyzer, 'manifest', 'version-code', str(APK)])
    run_capture('apkanalyzer-version-name', [apkanalyzer, 'manifest', 'version-name', str(APK)])
    run_capture('apkanalyzer-manifest-print', [apkanalyzer, 'manifest', 'print', str(APK)])

embedded = OUT / 'libXlorie-embedded.so'
run_capture('embedded-file', ['file', str(embedded)])
run_capture('embedded-readelf-h', ['readelf', '-h', str(embedded)])
run_capture('embedded-readelf-d', ['readelf', '-d', str(embedded)])
run_capture('embedded-readelf-n', ['readelf', '-n', str(embedded)])
run_capture('embedded-nm-d-u', ['nm', '-D', '-u', str(embedded)])
run_capture('embedded-nm-d-c', ['nm', '-D', '-C', str(embedded)])
run_capture('embedded-strings', ['strings', '-a', str(embedded)])

signer_text = (OUT / 'apksigner-verify.stdout.txt').read_text(errors='replace')
sha_match = re.search(r'Signer #1 certificate SHA-256 digest:\s*([^\s]+)', signer_text)
package_text = (OUT / 'apkanalyzer-application-id.stdout.txt').read_text(errors='replace') if apkanalyzer else ''
version_code_text = (OUT / 'apkanalyzer-version-code.stdout.txt').read_text(errors='replace') if apkanalyzer else ''
version_name_text = (OUT / 'apkanalyzer-version-name.stdout.txt').read_text(errors='replace') if apkanalyzer else ''
nm_text = (OUT / 'embedded-nm-d-u.stdout.txt').read_text(errors='replace')
strings_text = (OUT / 'embedded-strings.stdout.txt').read_text(errors='replace')
historical_symbols = [
    'xorg_backtrace', 'ExaDoPrepareAccess', 'create_bits_picture', 'fbComposite',
    'pixman_image_composite', 'loriePrepareAccess',
]
report = {
    'apk_path': str(APK),
    'apk_bytes': APK.stat().st_size,
    'apk_sha256': sha256(APK),
    'zip_report': str(OUT / 'apk-zip-report.json'),
    'package_analyzer': apkanalyzer,
    'package_name_observed': package_text.strip(),
    'package_exact_com_waydefu_x11gpu': package_text.strip() == 'com.waydefu.x11gpu',
    'version_code_observed': version_code_text.strip(),
    'version_name_observed': version_name_text.strip(),
    'apksigner_returncode': json.loads((OUT / 'apksigner-verify.status').read_text())['returncode'],
    'signer_sha256_digest': sha_match.group(1) if sha_match else None,
    'zipalign_returncode': json.loads((OUT / 'zipalign-check.status').read_text())['returncode'],
    'python_zip_stored_alignment': not zip_report['stored_misaligned_members'],
    'python_zip_misaligned_members': zip_report['stored_misaligned_members'],
    'embedded_library_sha256': sha256(embedded),
    'eglGetNativeClientBufferANDROID_undefined_census': 'eglGetNativeClientBufferANDROID' in nm_text,
    'historical_crash_sensitive_undefined_census': {symbol: symbol in nm_text for symbol in historical_symbols},
    'gatea_a1_marker_in_embedded_strings': 'GATEA_A1' in strings_text,
    'probe_symbol_in_embedded_dynamic_symbols': 'gateaA1MicroprobeRun' in (OUT / 'embedded-nm-d-c.stdout.txt').read_text(errors='replace'),
}
(OUT / 'apk-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
