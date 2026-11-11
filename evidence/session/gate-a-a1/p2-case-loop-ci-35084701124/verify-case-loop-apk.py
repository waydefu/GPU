#!/usr/bin/env python3
"""Qualify the hardened CASE_LOOP CI APK (run 35084701124, HEAD 7549e36)."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import zipfile

EVID = Path('/root/projects/GPU加速/evidence/session/gate-a-a1/p2-case-loop-ci-35084701124')
APK = EVID / 'apk' / 'termux-x11-universal-debug.apk'
OUT = EVID / 'apk-elf-verification'
OUT.mkdir(parents=True, exist_ok=True)
LIB_REL = 'lib/arm64-v8a/libXlorie.so'
EXPECTED_SIGNER = 'b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1'
EXPECTED_PKG = 'com.waydefu.x11gpu'
EXPECTED_HEAD = '7549e3667ec03b8b5e50d2e5befe03065840bbd9'
EXPECTED_HEAD_SHORT = '7549e36'
CI_RUN = 35084701124
PREVIOUS_FEEAA56_APK_SHA256 = 'a2d92ff9ecb948c5b3ac3c424727d12e97b9991f3b1b68d068a6828d744f3210'
GITHUB_ZIP_DIGEST = '3f7318b7964132d7e3017f3b5025ecaa80b465259ce62921d37ea35ffa2022b8'
AAPT = '/usr/bin/aapt'
APKSIGNER = '/usr/bin/apksigner'
APK_FOR_SIGNER = Path('/tmp/case-loop-7549e36-termux-x11-universal-debug.apk')
WT = Path('/root/projects/GPU加速/src/f8-ahb-gatea-case-loop')
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
    'GATEA_SUMMARY',
    'x-present-copy-wait',
    'TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL',
    'GATEA_FATAL_HALT',
)
FORBIDDEN_STRINGS = (
    'direct-to-legacy',
    'CPU fallback as PASS',
    'COND_WAIT_ENTER',
    'COND_WAIT_EXIT',
)
# Diagnostic stall-phase markers belong to feeaa56, not this 0d72332-based fix.
ABSENT_DIAGNOSTIC_STRINGS = (
    'STALL_PHASE phase=',
    'NOTIFY_ENTER',
    'NOTIFY_EXIT',
)
NM_REQUIRED = (
    'present_gpu_copy_retire_or_fatal',
)
NM_OPTIONAL = (
    'Renderer::waitWhileIdle',
)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def run_capture(label, args):
    result = subprocess.run(args, capture_output=True, check=False)
    (OUT / f'{label}.stdout.txt').write_bytes(result.stdout)
    (OUT / f'{label}.stderr.txt').write_bytes(result.stderr)
    (OUT / f'{label}.status').write_text(
        json.dumps({'argv': args, 'returncode': result.returncode}, indent=2) + '\n')
    return result.returncode, result.stdout.decode(errors='replace'), result.stderr.decode(errors='replace')


assert APK.is_file() and APK.stat().st_size > 0, APK
report = {
    'apk_path': str(APK),
    'apk_bytes': APK.stat().st_size,
    'apk_sha256': sha256(APK),
    'head': EXPECTED_HEAD,
    'ci_run': CI_RUN,
    'github_zip_digest_is_not_apk_sha256': GITHUB_ZIP_DIGEST,
}
assert report['apk_sha256'] != PREVIOUS_FEEAA56_APK_SHA256, 'downloaded previous feeaa56 APK'
assert report['apk_sha256'] != GITHUB_ZIP_DIGEST, 'used GitHub ZIP digest as APK SHA256'
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
    diag_absent = {key: (key not in out) for key in ABSENT_DIAGNOSTIC_STRINGS}
    strings[label] = {
        'required': present,
        'forbidden_absent': absent,
        'diagnostic_absent_as_expected': diag_absent,
    }
    assert all(present.values()), (label, present)
    assert all(absent.values()), (label, absent)
    assert all(diag_absent.values()), (label, diag_absent)
report['strings'] = strings

rc, out, _ = run_capture('unstripped-nm', ['nm', '-a', '-C', str(unstripped)])
assert rc == 0
nm_found = {sym: (sym in out) for sym in NM_REQUIRED}
nm_optional = {sym: (sym in out) for sym in NM_OPTIONAL}
report['nm'] = nm_found
report['nm_optional'] = nm_optional
assert all(nm_found.values()), nm_found

init = (WT / 'lorie/src/main/cpp/lorie/InitOutput.c').read_text()
renderer = (WT / 'lorie/src/main/cpp/lorie/renderer.cpp').read_text()
hdr = (WT / 'lorie/src/main/cpp/lorie/lorie.h').read_text()
idle_start = renderer.find('void Renderer::waitWhileIdle')
idle_end = renderer.find('void Renderer::threadLoop')
idle = renderer[idle_start:idle_end]
rinit_start = renderer.find('void Renderer::init(JNIEnv* env)')
rinit = renderer[rinit_start:renderer.find('int Renderer::getWakeupCondFd')]
report['wait_timeout_still_2000'] = 'lorieGpuCopyWait(serial, 2000)' in init
report['no_3000_workaround'] = 'lorieGpuCopyWait(serial, 3000)' not in init
report['helper_kept'] = 'lorieGpuCopyWaitForCompositeOrFatal' in init
report['frame_wait_8ms'] = '#define LORIE_RENDERER_FRAME_WAIT_NS 8000000L' in hdr
report['fence_timeout_unchanged'] = '#define LORIE_GATEA_FENCE_TIMEOUT_NS 2000000000ull' in hdr
report['idle_sticky_recheck'] = 'ObserveWriteIndex' in idle and idle.find('ObserveWriteIndex') < idle.find('pthread_cond_timedwait')
report['idle_monotonic'] = 'clock_gettime(CLOCK_MONOTONIC, &deadline)' in idle
report['idle_no_realtime'] = 'CLOCK_REALTIME' not in idle
report['init_monotonic_pshared'] = (
    'pthread_condattr_setpshared(&cond_attr, PTHREAD_PROCESS_SHARED)' in rinit
    and 'pthread_condattr_setclock(&cond_attr, CLOCK_MONOTONIC)' in rinit
    and 'abort()' in rinit
)
report['egl_forever_next_buffer'] = 'EGL_SYNC_FLUSH_COMMANDS_BIT_KHR, EGL_FOREVER' in renderer
report['test_env_default_off'] = 'setenv("TERMUX_X11_GATEA_TEST_FAULT"' not in init
assert report['wait_timeout_still_2000']
assert report['no_3000_workaround']
assert report['helper_kept']
assert report['frame_wait_8ms']
assert report['fence_timeout_unchanged']
assert report['idle_sticky_recheck']
assert report['idle_monotonic']
assert report['idle_no_realtime']
assert report['init_monotonic_pshared']
assert report['egl_forever_next_buffer']
assert report['test_env_default_off']

head = subprocess.check_output(['git', '-C', str(WT), 'rev-parse', 'HEAD'], text=True).strip()
assert head == EXPECTED_HEAD, head

rc, out, _ = run_capture('aapt-dump', [AAPT, 'dump', 'badging', str(APK)])
assert rc == 0, out
pkg = re.search(r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", out)
assert pkg, out[:500]
report['package'] = pkg.group(1)
report['versionCode'] = pkg.group(2)
report['versionName'] = pkg.group(3)
assert report['package'] == EXPECTED_PKG
assert EXPECTED_HEAD_SHORT in report['versionName'], report['versionName']
assert report['package'] != 'com.termux.x11'

shutil.copy2(APK, APK_FOR_SIGNER)
rc, out, _ = run_capture('apksigner', [APKSIGNER, 'verify', '--verbose', '--print-certs', str(APK_FOR_SIGNER)])
certs = [c.lower() for c in re.findall(r'SHA-256 digest:\s*([0-9a-fA-F]+)', out)]
report['apksigner_rc'] = rc
report['signer_sha256'] = certs[0] if certs else None
assert rc == 0 and EXPECTED_SIGNER in certs, certs

(OUT / 'p2-case-loop-apk-elf-report.json').write_text(json.dumps(report, indent=2) + '\n')
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
    'nm': report['nm'],
    'nm_optional': report['nm_optional'],
    'wait_timeout_still_2000': report['wait_timeout_still_2000'],
    'idle_sticky_recheck': report['idle_sticky_recheck'],
    'idle_monotonic': report['idle_monotonic'],
    'init_monotonic_pshared': report['init_monotonic_pshared'],
}, indent=2))
