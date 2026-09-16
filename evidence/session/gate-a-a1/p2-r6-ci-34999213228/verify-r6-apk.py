#!/usr/bin/env python3
"""Gate A P2 R6 CI artifact verifier (run 34999213228, HEAD 0f1e546)."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import zipfile

EVID = Path('/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r6-ci-34999213228')
APK = EVID / 'apk' / 'termux-x11-universal-debug.apk'
OUT = EVID / 'apk-elf-verification'
OUT.mkdir(parents=True, exist_ok=True)
LIB_REL = 'lib/arm64-v8a/libXlorie.so'
EXPECTED_SIGNER = 'b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1'
SDK_BT = '/root/android-sdk/build-tools/36.0.0'
APKANALYZER = '/root/android-sdk/cmdline-tools/latest/bin/apkanalyzer'
EXPECTED_PKG = 'com.waydefu.x11gpu'
EXPECTED_HEAD = '0f1e54699d0b11a781f2c044fbc77505f8a53bd8'
CI_RUN = 34999213228
EXPECTED_APK_SHA256 = '2bc4c8ba2b6a11928a3a6b76e04fcd9acf0bacfe11f88afd0a698c8c81b10851'
EXPECTED_BUILD_ID = '263bee5f7d41087b0bd7fa180d47fdafd12b2ecf'
EXPECTED_ABIS = (
    'lib/arm64-v8a/libXlorie.so',
    'lib/armeabi-v7a/libXlorie.so',
    'lib/x86/libXlorie.so',
    'lib/x86_64/libXlorie.so',
)


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
          'apk_sha256': sha256(APK), 'head': EXPECTED_HEAD,
          'ci_run': CI_RUN}
assert report['apk_sha256'] == EXPECTED_APK_SHA256, report['apk_sha256']
run_meta = json.loads((EVID / 'run.json').read_text())
assert run_meta['headSha'] == EXPECTED_HEAD, run_meta
assert run_meta['conclusion'] == 'success', run_meta
assert run_meta['event'] == 'workflow_dispatch', run_meta
report['ci_headSha'] = run_meta['headSha']
report['ci_event'] = run_meta['event']
report['ci_url'] = run_meta['url']

with zipfile.ZipFile(APK) as zf:
    infos = zf.infolist()
    names = [i.filename for i in infos]
    report['testzip'] = zf.testzip()
    report['member_count'] = len(infos)
    report['duplicate_names'] = sorted({n for n in names if names.count(n) > 1})
    report['libxlories'] = sorted(n for n in names if n.endswith('libXlorie.so'))
    report['arm64_member_present'] = LIB_REL in names
    report['expected_abis_present'] = all(n in names for n in EXPECTED_ABIS)
    stored = [i for i in infos if i.compress_type == zipfile.ZIP_STORED]
    bad = 0
    with open(APK, 'rb') as f:
        for i in stored:
            f.seek(i.header_offset)
            local = f.read(30)
            if len(local) < 30:
                bad += 1
                continue
            name_len = int.from_bytes(local[26:28], 'little')
            extra_len = int.from_bytes(local[28:30], 'little')
            if (i.header_offset + 30 + name_len + extra_len) % 4 != 0:
                bad += 1
    report['stored_count'] = len(stored)
    report['stored_mod4_failures'] = bad

assert report['expected_abis_present'], report['libxlories']

with zipfile.ZipFile(APK) as zf:
    embedded = OUT / 'libXlorie-embedded.so'
    embedded.write_bytes(zf.read(LIB_REL))
report['embedded_sha256'] = sha256(embedded)

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
assert build_ids['embedded'] == EXPECTED_BUILD_ID, build_ids

p0wanted = {'GATEA_A1': 'A1 microprobe marker',
            'gateaA1MicroprobeRun': 'A1 entry, unstripped only (hidden)'}
p1wanted = {'TERMUX_X11_GATEA_PROTO': 'P1/P2 flag literal',
            'GATEA_FATAL_HALT': 'fatal-halt log tag'}
telewanted = {'TERMUX_X11_GATEA_TELEMETRY': 'telemetry exact-opt-in flag'}
b1b4lits = {
    'r-gatea-DIRECT_LOOKUP_FAIL': 'B2 lookup-miss fatal',
    'r-gatea-stale-direct-meta': 'B2 stale-meta fatal',
    'r-gatea-direct-identity': 'B2 identity mismatch fatal',
    'x-direct-slot-not-consumed': 'B2 slot-reuse fatal',
    'x-direct-not-success': 'post-publish fail-stop tag',
    'x-post-unlock-revalidate': 'pair-lease revalidation tag',
    'r-gatea-fence-wait': 'finite-fence failure tag',
    'x-publish-no-lease': 'lease refusal tag',
    'x-unregister-send': 'B4 unregister send fatal',
    'x-generation-close-send': 'B4 generation close send fatal',
    'r-unregister-missing': 'B4 renderer unregister miss',
    'r-close-not-empty': 'B4 generation close empty check',
}
diaglits = {
    'Uraw': 'raw ucontext qword dump marker',
    'Upid pid': 'pid/tid crash marker',
}
repairlits = {
    'r-rebind-busy': 'Activity bind-from-shared-state fail-stop',
    'GATEA_BIND': 'bind tuple diagnostic log',
    'GATEA_PEEK': 'peek/bound diagnostic log',
    'GATEA_HANDLE': 'handled-frame diagnostic log',
    'r-unbound-frame': 'peek-true unbound fail-closed halt',
    'GATEA_DRAIN': 'GL-thread pending-import drain log',
}
xpumplits = {
    'x-pump-hup': 'X pump peer closed during waiter',
    'x-pump-io': 'X pump I/O error during waiter',
    'x-pump-protocol': 'X pump protocol fatal during waiter',
    'x-deferred-record-queue': 'deferred legacy queue overflow fatal',
    'x-legacy-record-dispatch': 'legacy dispatch fatal during pump',
    'x-wait-clock': 'waiter CLOCK_MONOTONIC failure',
}
terminallits = {
    'r-tuple-mismatch': 'REGISTER tuple mismatch fatal',
    'r-failed-send': 'REGISTER_FAILED send fatal',
    'r-duplicate-ready': 'duplicate READY fatal',
    'x-fatal-after-timeout': 'X last-fatal read before timeout',
    'GATEA_VALIDATE': 'post-drain VALIDATE log tag',
    'VALIDATE_ENTER': 'VALIDATE stage enter',
    'TUPLE_MATCH': 'VALIDATE bound-tuple match',
    'TUPLE_MISMATCH': 'VALIDATE bound-tuple mismatch',
    'EGL_DISPLAY_PRESENT': 'VALIDATE EGL display present',
    'EGL_NO_DISPLAY': 'VALIDATE EGL no display',
    'EGL_CONTEXT_PRESENT': 'VALIDATE EGL context present',
    'EGL_NO_CONTEXT': 'VALIDATE EGL no context',
    'NATIVE_CLIENT_BUFFER_CAPABLE': 'VALIDATE native client buffer cap',
    'CLIENT_BUFFER_ENTER': 'VALIDATE client buffer enter',
    'CLIENT_BUFFER_RETURN': 'VALIDATE client buffer return',
    'CREATE_IMAGE_ENTER': 'VALIDATE eglCreateImage enter',
    'CREATE_IMAGE_RETURN': 'VALIDATE eglCreateImage return',
    'TEXTURE_CREATE_RETURN': 'VALIDATE glGenTextures return',
    'IMAGE_TARGET_ENTER': 'VALIDATE image-target enter',
    'IMAGE_TARGET_RETURN': 'VALIDATE image-target return',
    'READY_SEND_ENTER': 'VALIDATE READY send enter',
    'READY_SEND_RETURN': 'VALIDATE READY send return',
    'FAILED_SEND_ENTER': 'VALIDATE FAILED send enter',
    'FAILED_SEND_RETURN': 'VALIDATE FAILED send return',
    'VALIDATE_TERMINAL_READY': 'VALIDATE READY terminal',
    'VALIDATE_TERMINAL_FAILED': 'VALIDATE FAILED terminal',
    'VALIDATE_TERMINAL_FATAL': 'VALIDATE FATAL terminal',
}
forbidden = {
    'direct-to-legacy': 'direct-to-legacy fallback',
    'CPU fallback as PASS': 'CPU fallback pass wording',
    'TERMUX_X11_GATEA_TEST_FAULT': 'R7 fault hook must stay absent',
}
r6lits = {
    'TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL': 'R6 Present OOM one-shot getenv',
    'x-present-copy-wait': 'Present wait-or-fatal halt tag',
}
p2syms = [
    'consumeGateAComposite', 'gateAEnsureReady', 'gateADirectTryPrepare',
    'gateADirectPublishRect', 'gateADoneDirect', 'gateAPairRelockCpu',
    'gateAWaitTerminal', 'gateALookupDirect', 'gateAPairUndoReserve',
    'gateAReadyStill', 'gateAPairOverlapsBuffer',
    'gateAQueueSemanticallyQuiescent', 'gateARetireBuffer',
    'gateACloseGeneration', 'gateADestroyReadyImport',
    'lorieGateAPublishDirectMeta', 'lorieGateAConsumeDirectMeta',
    'lorieGateABoundTuple', 'gateABindFromState', 'gateAHasPendingDrain',
    'p2a3CrashHandler', 'p2a3DumpUraw', 'p2a3PutHex64',
    'lorieGateAPumpConnection', 'lorieActivitySendGateFrame',
    'lorieActivitySendLegacyRecord', 'lorieActivitySendLegacyFd',
    'lorieActivitySendLegacyPayload',
    'lorieGateATraceXRequest', 'lorieGateATraceXCallback',
    'lorieGateAPresentRequeueShouldFail',
    'lorieGateATracePresentRequeueFailed',
    'lorieGateATracePresentAckAfterCompleted',
    'lorieGpuCopyWaitForPresentOrFatal',
    'lorieGateATracePresentEarlyAck',
    'present_gpu_copy_retire_or_fatal',
]
keys = (list(p0wanted) + list(p1wanted) + list(telewanted)
        + list(b1b4lits) + list(diaglits) + list(repairlits)
        + list(terminallits) + list(xpumplits) + list(r6lits)
        + list(forbidden))
strings = {}
for label, path in (('embedded', embedded), ('unstripped', unstripped)):
    rc, out, _ = run_capture(f'{label}-strings', ['strings', '-a', str(path)])
    assert rc == 0, label
    strings[label] = {key: (key in out) for key in keys}
report['strings'] = strings
report['p0_continuity'] = {
    'GATEA_A1_both': strings['embedded']['GATEA_A1'] and strings['unstripped']['GATEA_A1'],
    'entry_unstripped_only': (not strings['embedded']['gateaA1MicroprobeRun'])
    and strings['unstripped']['gateaA1MicroprobeRun'],
}
assert report['p0_continuity']['GATEA_A1_both'], 'P0/A1 continuity broken'
assert report['p0_continuity']['entry_unstripped_only'], 'A1 visibility changed'
report['p1_continuity'] = {
    'flag_both': strings['embedded']['TERMUX_X11_GATEA_PROTO']
    and strings['unstripped']['TERMUX_X11_GATEA_PROTO'],
    'halt_both': strings['embedded']['GATEA_FATAL_HALT']
    and strings['unstripped']['GATEA_FATAL_HALT'],
}
assert report['p1_continuity']['flag_both'], 'P1 flag literal missing'
assert report['p1_continuity']['halt_both'], 'P1 halt tag missing'
report['telemetry_literals'] = {
    'embedded': strings['embedded']['TERMUX_X11_GATEA_TELEMETRY'],
    'unstripped': strings['unstripped']['TERMUX_X11_GATEA_TELEMETRY'],
}
assert report['telemetry_literals']['embedded'] and report['telemetry_literals']['unstripped']
report['b1b4_literals'] = {
    'embedded': {k: strings['embedded'][k] for k in b1b4lits},
    'unstripped': {k: strings['unstripped'][k] for k in b1b4lits},
}
assert all(report['b1b4_literals']['embedded'].values()), report['b1b4_literals']['embedded']
assert all(report['b1b4_literals']['unstripped'].values()), report['b1b4_literals']['unstripped']
report['diag_literals'] = {
    'embedded': {k: strings['embedded'][k] for k in diaglits},
    'unstripped': {k: strings['unstripped'][k] for k in diaglits},
}
assert all(report['diag_literals']['embedded'].values()), report['diag_literals']['embedded']
assert all(report['diag_literals']['unstripped'].values()), report['diag_literals']['unstripped']
report['repair_literals'] = {
    'embedded': {k: strings['embedded'][k] for k in repairlits},
    'unstripped': {k: strings['unstripped'][k] for k in repairlits},
}
assert all(report['repair_literals']['embedded'].values()), report['repair_literals']['embedded']
assert all(report['repair_literals']['unstripped'].values()), report['repair_literals']['unstripped']
report['terminal_literals'] = {
    'embedded': {k: strings['embedded'][k] for k in terminallits},
    'unstripped': {k: strings['unstripped'][k] for k in terminallits},
}
assert all(report['terminal_literals']['embedded'].values()), report['terminal_literals']['embedded']
assert all(report['terminal_literals']['unstripped'].values()), report['terminal_literals']['unstripped']
report['xpump_literals'] = {
    'embedded': {k: strings['embedded'][k] for k in xpumplits},
    'unstripped': {k: strings['unstripped'][k] for k in xpumplits},
}
assert all(report['xpump_literals']['embedded'].values()), report['xpump_literals']['embedded']
assert all(report['xpump_literals']['unstripped'].values()), report['xpump_literals']['unstripped']
report['r6_literals'] = {
    'embedded': {k: strings['embedded'][k] for k in r6lits},
    'unstripped': {k: strings['unstripped'][k] for k in r6lits},
}
assert all(report['r6_literals']['embedded'].values()), report['r6_literals']['embedded']
assert all(report['r6_literals']['unstripped'].values()), report['r6_literals']['unstripped']
report['forbidden_absent'] = {
    'embedded': {k: (not strings['embedded'][k]) for k in forbidden},
    'unstripped': {k: (not strings['unstripped'][k]) for k in forbidden},
}
assert all(report['forbidden_absent']['embedded'].values()), report['forbidden_absent']['embedded']
assert all(report['forbidden_absent']['unstripped'].values()), report['forbidden_absent']['unstripped']

rc, out, _ = run_capture('unstripped-nm-gatea',
                         ['nm', '-a', '-C', str(unstripped)])
gatea_syms = [line for line in out.splitlines()
              if 'orieGateA' in line or 'gatea' in line.lower()
              or 'gateA' in line or 'GateADirect' in line or 'GateAPair' in line
              or 'p2a3' in line or 'lorieActivitySend' in line
              or 'GpuCopyWaitForPresent' in line
              or 'present_gpu_copy_retire' in line]
(OUT / 'unstripped-nm-gatea-symbols.txt').write_text('\n'.join(gatea_syms) + '\n')
found = set()
for line in gatea_syms:
    for s in p2syms:
        if s in line:
            found.add(s)
report['p2_symbols_expected'] = sorted(p2syms)
report['p2_symbols_found'] = sorted(found)
report['p2_symbols_missing_informational'] = sorted(set(p2syms) - found)
assert 'p2a3CrashHandler' in found, 'crash handler missing from unstripped nm'
assert 'lorieGateABoundTuple' in found, 'bound-tuple symbol missing from unstripped nm'
assert 'lorieGateAPumpConnection' in found, 'pump symbol missing from unstripped nm'
assert 'lorieActivitySendGateFrame' in found, 'gate writer missing from unstripped nm'
assert 'lorieGateATraceXRequest' in found, 'R6 request trace missing from unstripped nm'
assert 'lorieGateATraceXCallback' in found, 'R6 callback trace missing from unstripped nm'
assert 'lorieGateAPresentRequeueShouldFail' in found, 'R6 Present OOM helper missing'
assert 'lorieGateATracePresentRequeueFailed' in found, 'R6 requeue-fail trace missing'
assert 'lorieGateATracePresentAckAfterCompleted' in found, 'R6 ack-after-completed missing'
assert 'lorieGpuCopyWaitForPresentOrFatal' in found, 'Present wait-or-fatal missing'
assert 'present_gpu_copy_retire_or_fatal' in found, 'Present retirement helper missing'
# Early-ACK tracer is source-kept but unused after wait-or-fatal; --gc-sections
# drops it. Event 32 remains forbidden in the judge. Do not require nm.
# WaiterObserve / TelemetryPublished / TelemetryRequested are
# static inline __always_inline; nm-missing is expected, same class as
# other header helpers. Totality is proven by GATEA_VALIDATE / halt
# literals plus absence of the old getenv helper symbol.
assert 'lorieGateATelemetryEnabled' not in out, 'old getenv telemetry helper still present'

manifest = {}
for label, sub in (('application-id', 'application-id'), ('version-code', 'version-code'),
                   ('version-name', 'version-name')):
    rc, out, _ = run_capture(f'manifest-{label}', [APKANALYZER, 'manifest', sub, str(APK)])
    manifest[label] = {'returncode': rc, 'value': out.strip()}
report['manifest'] = manifest
assert manifest['application-id']['value'] == EXPECTED_PKG, manifest['application-id']
assert 'com.termux.x11' != manifest['application-id']['value']
assert '0f1e546' in manifest['version-name']['value'], manifest['version-name']

rc, out, _ = run_capture('apksigner-verify', [f'{SDK_BT}/apksigner', 'verify',
                                              '--verbose', '--print-certs', str(APK)])
report['apksigner_returncode'] = rc
certs = re.findall(r'SHA-256 digest:\s*([0-9a-fA-F]+)', out)
report['signer_sha256_list'] = [c.lower() for c in certs]
report['signer_expected_cert_present'] = EXPECTED_SIGNER in report['signer_sha256_list']
assert rc == 0 and report['signer_expected_cert_present']

za = Path(f'{SDK_BT}/zipalign')
report['formal_zipalign'] = {
    'path': str(za),
    'blocked_reason': 'x86-64 tool on aarch64 host',
    'claimed_pass': False,
}

(OUT / 'p2-r6-apk-elf-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({
    'apk_sha256': report['apk_sha256'],
    'apk_bytes': report['apk_bytes'],
    'package': manifest['application-id']['value'],
    'versionCode': manifest['version-code']['value'],
    'versionName': manifest['version-name']['value'],
    'abis': report['libxlories'],
    'testzip': report['testzip'],
    'members': report['member_count'],
    'duplicates': report['duplicate_names'],
    'stored': f"{report['stored_count']}/{report['stored_count'] - report['stored_mod4_failures']} aligned failures={report['stored_mod4_failures']}",
    'signer': report['signer_expected_cert_present'],
    'build_ids': report['build_ids'],
    'build_id_equal': report['build_id_equal'],
    'p0': report['p0_continuity'],
    'p1': report['p1_continuity'],
    'telemetry': report['telemetry_literals'],
    'b1b4_lits_ok': all(report['b1b4_literals']['embedded'].values()),
    'diag_lits_ok': all(report['diag_literals']['embedded'].values()),
    'repair_lits_ok': all(report['repair_literals']['embedded'].values()),
    'terminal_lits_ok': all(report['terminal_literals']['embedded'].values()),
    'xpump_lits_ok': all(report['xpump_literals']['embedded'].values()),
    'r6_lits_ok': all(report['r6_literals']['embedded'].values()),
    'forbidden_absent': report['forbidden_absent'],
    'syms_found': report['p2_symbols_found'],
    'syms_missing': report['p2_symbols_missing_informational'],
}, indent=2))
