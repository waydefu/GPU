#!/usr/bin/env python3
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import re
import subprocess

EVIDENCE = Path('/root/projects/GPU加速/evidence/session/gate-a-a1')
RUN_ID = '34688831275'
ARTIFACT_ROOT = EVIDENCE / 'artifacts' / RUN_ID
EMBEDDED_REPORT = EVIDENCE / 'apk-verification' / 'apk-report.json'
OUT = EVIDENCE / 'elf-verification'
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


candidates = sorted(ARTIFACT_ROOT.glob('**/obj/arm64-v8a/libXlorie.so'))
assert len(candidates) == 1, candidates
unstripped = candidates[0]
assert unstripped.is_file() and unstripped.stat().st_size > 0
embedded = EVIDENCE / 'apk-verification' / 'libXlorie-embedded.so'
assert embedded.is_file()

run_capture('unstripped-file', ['file', str(unstripped)])
run_capture('unstripped-readelf-h', ['readelf', '-h', str(unstripped)])
run_capture('unstripped-readelf-d', ['readelf', '-d', str(unstripped)])
run_capture('unstripped-readelf-n', ['readelf', '-n', str(unstripped)])
run_capture('unstripped-nm-d-u', ['nm', '-D', '-u', str(unstripped)])
run_capture('unstripped-nm-a-c', ['nm', '-a', '-C', str(unstripped)])
run_capture('unstripped-strings', ['strings', '-a', str(unstripped)])

embedded_notes = (EVIDENCE / 'apk-verification' / 'embedded-readelf-n.stdout.txt').read_text(errors='replace')
unstripped_notes = (OUT / 'unstripped-readelf-n.stdout.txt').read_text(errors='replace')
embedded_build_id = re.search(r'Build ID:\s*([0-9a-f]+)', embedded_notes)
unstripped_build_id = re.search(r'Build ID:\s*([0-9a-f]+)', unstripped_notes)
assert embedded_build_id and unstripped_build_id, (embedded_notes, unstripped_notes)
assert embedded_build_id.group(1) == unstripped_build_id.group(1), (
    embedded_build_id.group(1), unstripped_build_id.group(1))

embedded_nm_u = (EVIDENCE / 'apk-verification' / 'embedded-nm-d-u.stdout.txt').read_text(errors='replace')
unstripped_nm_u = (OUT / 'unstripped-nm-d-u.stdout.txt').read_text(errors='replace')
unstripped_nm_all = (OUT / 'unstripped-nm-a-c.stdout.txt').read_text(errors='replace')
unstripped_strings = (OUT / 'unstripped-strings.stdout.txt').read_text(errors='replace')
unstripped_dynamic = (OUT / 'unstripped-readelf-d.stdout.txt').read_text(errors='replace')
embedded_header = (EVIDENCE / 'apk-verification' / 'embedded-readelf-h.stdout.txt').read_text(errors='replace')
unstripped_header = (OUT / 'unstripped-readelf-h.stdout.txt').read_text(errors='replace')

historical_symbols = [
    'xorg_backtrace', 'ExaDoPrepareAccess', 'create_bits_picture', 'fbComposite',
    'pixman_image_composite', 'loriePrepareAccess',
]
report = {
    'unstripped_path': str(unstripped),
    'unstripped_bytes': unstripped.stat().st_size,
    'unstripped_sha256': sha256(unstripped),
    'embedded_path': str(embedded),
    'embedded_bytes': embedded.stat().st_size,
    'embedded_sha256': sha256(embedded),
    'embedded_sha256_from_apk_report': json.loads(EMBEDDED_REPORT.read_text())['embedded_library_sha256'],
    'embedded_file_arm64': 'ARM aarch64' in (EVIDENCE / 'apk-verification' / 'embedded-file.stdout.txt').read_text(errors='replace'),
    'unstripped_file_arm64': 'ARM aarch64' in (OUT / 'unstripped-file.stdout.txt').read_text(errors='replace'),
    'embedded_readelf_machine_aarch64': 'Machine:                           AArch64' in embedded_header,
    'unstripped_readelf_machine_aarch64': 'Machine:                           AArch64' in unstripped_header,
    'embedded_build_id': embedded_build_id.group(1),
    'unstripped_build_id': unstripped_build_id.group(1),
    'build_id_match': embedded_build_id.group(1) == unstripped_build_id.group(1),
    'embedded_dt_needed': re.findall(r'Shared library: \[([^]]+)\]', (EVIDENCE / 'apk-verification' / 'embedded-readelf-d.stdout.txt').read_text(errors='replace')),
    'unstripped_dt_needed': re.findall(r'Shared library: \[([^]]+)\]', unstripped_dynamic),
    'embedded_forbidden_full_libX11': 'libX11' in (EVIDENCE / 'apk-verification' / 'embedded-readelf-d.stdout.txt').read_text(errors='replace'),
    'unstripped_forbidden_full_libX11': 'libX11' in unstripped_dynamic,
    'embedded_eglGetNativeClientBufferANDROID_undefined': 'eglGetNativeClientBufferANDROID' in embedded_nm_u,
    'unstripped_eglGetNativeClientBufferANDROID_undefined': 'eglGetNativeClientBufferANDROID' in unstripped_nm_u,
    'embedded_historical_undefined': {symbol: symbol in embedded_nm_u for symbol in historical_symbols},
    'unstripped_historical_undefined': {symbol: symbol in unstripped_nm_u for symbol in historical_symbols},
    'gatea_a1_marker_embedded_strings': 'GATEA_A1' in (EVIDENCE / 'apk-verification' / 'embedded-strings.stdout.txt').read_text(errors='replace'),
    'gatea_a1_marker_unstripped_strings': 'GATEA_A1' in unstripped_strings,
    'gatea_a1_probe_symbol_unstripped_nm': 'gateaA1MicroprobeRun' in unstripped_nm_all,
    'gatea_a1_probe_symbol_embedded_dynamic_nm': 'gateaA1MicroprobeRun' in (EVIDENCE / 'apk-verification' / 'embedded-nm-d-c.stdout.txt').read_text(errors='replace'),
    'source_probe_body_in_head': 'extern "C" void gateaA1MicroprobeRun' in subprocess.run(
        ['git', 'show', 'HEAD:lorie/src/main/cpp/lorie/gatea_a1_microprobe.cpp'],
        cwd='/root/projects/GPU加速/src/f8-ahb-gatea-a1', capture_output=True, text=True, check=True).stdout,
}
assert report['embedded_sha256'] == report['embedded_sha256_from_apk_report']
assert report['embedded_readelf_machine_aarch64'] and report['unstripped_readelf_machine_aarch64']
assert report['build_id_match']
assert not report['embedded_forbidden_full_libX11']
assert not report['unstripped_forbidden_full_libX11']
assert report['gatea_a1_marker_embedded_strings']
assert report['gatea_a1_marker_unstripped_strings']
assert report['source_probe_body_in_head']
(OUT / 'elf-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
