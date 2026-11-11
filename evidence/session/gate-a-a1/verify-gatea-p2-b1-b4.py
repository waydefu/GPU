#!/usr/bin/env python3
"""Static regression gate for Gate A P2 B1-B4 correction.

This is intentionally source-structural because device/runtime execution is out
of scope for this implementation round. Native builds remain the compile gate.
"""
from pathlib import Path
import re

ROOT = Path('/root/projects/GPU加速/src/f8-ahb-gatea-a1/lorie/src/main/cpp/lorie')
h = (ROOT / 'lorie.h').read_text()
r = (ROOT / 'renderer.cpp').read_text()
x = (ROOT / 'InitOutput.c').read_text()
c = (ROOT / 'cmdentrypoint.cpp').read_text()
a = (ROOT / 'activity.cpp').read_text()

checks = []
def check(name: str, ok: bool) -> None:
    checks.append((name, bool(ok)))

check('queue ABI remains 168', 'sizeof(LorieGpuCopyEntry) == 168' in h)
check('P0 sideband remains 40', 'sizeof(struct LorieGateAProtocol) == 40' in h)
check('direct side metadata declared', 'struct LorieGateADirectMeta' in h and 'gateADirect[' in h)
check('direct metadata release/acquire helpers',
      'lorieGateAPublishDirectMeta' in h and 'lorieGateAObserveDirectMeta' in h)
check('renderer identifies direct by side metadata',
      'lorieGateAObserveDirectMeta' in r and
      not re.search(r'entry\.op\s*==\s*LORIE_GPU_OP_COMPOSITE\s*\n\s*&&\s*gateAIsReady', r))
check('direct lookup failure is explicit', 'DIRECT_LOOKUP_FAIL' in r)
check('direct consume telemetry exists', 'LORIE_GATEA_EVENT_CONSUME_DIRECT' in r)
check('direct branch publishes readIndex',
      r.count('lorieGateAPublishReadIndex(&state->gpuCopyQueue.readIndex, ri + 1)') >= 2)
check('every reserve globally quiescent',
      'if (!gateAUsed)' not in x and 'gateAQueueSemanticallyQuiescent' in x)
check('X unregister sender exists', 'lorieGateASendUnregister' in c)
check('X generation close sender exists', 'lorieGateASendGenerationClose' in c)
check('renderer receives unregister', 'LORIE_GATEA_MSG_UNREGISTER' in a and 'gateAEnqueueControl' in a)
check('renderer receives generation close', 'LORIE_GATEA_MSG_GENERATION_CLOSE' in a)
check('renderer GL-thread destroys resources',
      'gateADestroyReadyImport' in r and 'gateADrainPendingControls' in r)
check('X handles unregister ack', 'case LORIE_GATEA_MSG_UNREGISTER_ACK' in c)
check('X handles generation closed', 'case LORIE_GATEA_MSG_GENERATION_CLOSED' in c)
check('buffer retirement wired', 'gateARetireBuffer' in x)
check('generation close wired', 'gateACloseGeneration' in x)
check('telemetry default-off helper',
      'TERMUX_X11_GATEA_TELEMETRY' in h and 'lorieGateATelemetryEnabled' in h)
for event in (
    'REGISTER_READY', 'LEASE_RESERVED', 'UNLOCK_SRC_OK', 'UNLOCK_DST_OK',
    'LEASE_GPU_OWNED', 'PUBLISH', 'CONSUME_DIRECT', 'DIRECT_LOOKUP_OK',
    'DIRECT_LOOKUP_FAIL', 'DRAW_SUBMIT', 'FENCE_SATISFIED', 'FENCE_TIMEOUT',
    'FENCE_ERROR', 'COMPLETED_SERIAL', 'FIRST_FAILED_SERIAL',
    'GENERATION_FATAL', 'SEMANTIC_SUCCESS', 'RELOCK_SRC', 'RELOCK_DST',
    'REPAIR', 'ACK', 'PENDING_DEC', 'LEASE_RELEASE', 'UNREGISTER_SEND',
    'UNREGISTER_ACK', 'RESOURCE_DESTROY', 'GENERATION_CLOSE',
    'GENERATION_CLOSED'):
    check(f'event {event}', f'LORIE_GATEA_EVENT_{event}' in h)
for counter in (
    'DIRECT_PUBLISH', 'DIRECT_CONSUME', 'DIRECT_LOOKUP', 'DIRECT_LOOKUP_FAIL',
    'DIRECT_DRAW', 'FENCE_SATISFIED', 'SEMANTIC_SUCCESS',
    'DIRECT_TO_LEGACY', 'RELOCK', 'REPAIR', 'ACK', 'PENDING_DEC',
    'AHB_ACQUIRE', 'AHB_RELEASE', 'EGLIMAGE_CREATE', 'EGLIMAGE_DESTROY',
    'TEXTURE_CREATE', 'TEXTURE_DELETE', 'X_REGISTRY_CURRENT',
    'RENDERER_REGISTRY_CURRENT', 'LEASE_CURRENT'):
    token = counter
    check(f'counter {token}', f'LORIE_GATEA_COUNTER_{token}' in h)

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(('PASS ' if ok else 'FAIL ') + name)
print(f'SUMMARY total={len(checks)} failed={len(failed)}')
if failed:
    raise SystemExit(1)
