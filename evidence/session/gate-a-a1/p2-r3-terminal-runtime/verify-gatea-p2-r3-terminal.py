#!/usr/bin/env python3
"""Source-level RED→GREEN verifier for Gate A P2 R3 post-drain totality.

Fails on 8479997 control flow (silent tuple drop, FAILED-send log-only,
duplicate READY without halt, timeout without last fatal acquire, renderer
trace gated by process-local getenv). Passes only when those branches are
closed. Not a symbol-presence check.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT_DEFAULT = Path('/root/projects/GPU加速/src/f8-ahb-gatea-a1/lorie/src/main/cpp/lorie')


def extract_func(src: str, name: str) -> str:
    pat = re.compile(
        rf'(?:^|\n)(?:static\s+)?(?:__attribute__\(\(noreturn\)\)\s+)?'
        rf'(?:[\w*]+\s+)+{re.escape(name)}\s*\('
    )
    m = pat.search(src)
    if not m:
        raise SystemExit(f'missing function {name}')
    brace = src.find('{', m.end())
    if brace < 0:
        raise SystemExit(f'no body for {name}')
    depth = 0
    for idx in range(brace, len(src)):
        if src[idx] == '{':
            depth += 1
        elif src[idx] == '}':
            depth -= 1
            if depth == 0:
                return src[m.start():idx + 1]
    raise SystemExit(f'unclosed function {name}')


def first_if_body(src: str, predicate: str) -> str:
    m = re.search(predicate, src)
    if not m:
        raise SystemExit(f'missing predicate {predicate}')
    brace = src.find('{', m.end())
    if brace < 0:
        raise SystemExit(f'no brace after {predicate}')
    depth = 0
    for idx in range(brace, len(src)):
        if src[idx] == '{':
            depth += 1
        elif src[idx] == '}':
            depth -= 1
            if depth == 0:
                return src[brace:idx + 1]
    raise SystemExit(f'unclosed predicate {predicate}')


def check(name: str, ok: bool, checks: list) -> None:
    checks.append((name, bool(ok)))


def fatal_containment(text: str) -> bool:
    return ('gateARendererFatal' in text) or ('lorieGateAFatalHalt' in text)


def verify(h: str, r: str, x: str) -> int:
    checks: list[tuple[str, bool]] = []
    validate = extract_func(r, 'gateAValidateImport')
    send_failed = extract_func(r, 'gateASendRegisterFailed')
    ensure = extract_func(x, 'gateAEnsureReady')
    trace = extract_func(h, 'lorieGateATrace')
    counter = extract_func(h, 'lorieGateACounterAdd')

    mismatch = first_if_body(
        validate,
        r'if\s*\(\s*!lorieGateABoundTuple\s*\(\s*&bn\s*,\s*&bg\s*\)'
        r'\s*\|\|\s*bn\s*!=\s*nonce\s*\|\|\s*bg\s*!=\s*generation\s*\)')
    check('tuple mismatch fail-stops after cleanup',
          'gateAReleaseTrackedAhb' in mismatch
          and fatal_containment(mismatch)
          and 'return;' not in mismatch, checks)

    check('REGISTER_FAILED send failure fail-stops',
          fatal_containment(send_failed)
          and 'generation doomed via HUP path' not in send_failed
          and 'r-failed-send' in send_failed, checks)

    dup = first_if_body(
        validate,
        r'if\s*\(\s*i\s*<\s*LORIE_GATEA_MAX_READY\s*\)')
    check('duplicate READY uses renderer fatal containment',
          'duplicate' in dup.lower() and 'ready' in dup.lower()
          and fatal_containment(dup)
          and 'return;' not in dup, checks)
    check('duplicate READY does not publish-and-return',
          'lorieGateAPublishFatal' not in dup
          or fatal_containment(dup), checks)

    timeout_at = ensure.find('now.tv_sec > deadline.tv_sec')
    halt_at = ensure.find('x-ready-timeout', timeout_at)
    check('timeout condition and x-ready-timeout exist',
          timeout_at >= 0 and halt_at > timeout_at, checks)
    timeout_window = ensure[timeout_at:halt_at] if timeout_at >= 0 and halt_at > timeout_at else ''
    check('timeout acquires fatal before x-ready-timeout',
          'lorieGateAObserveFatal' in timeout_window, checks)
    check('timeout observes waiter terminal state before declaring timeout',
          'lorieGateAWaiterObserve' in timeout_window, checks)

    check('renderer trace is not getenv-gated',
          'getenv' not in trace
          and 'lorieGateATelemetryEnabled' not in trace
          and 'lorieGateATelemetryRequested' not in trace, checks)
    check('renderer trace uses published shared enable',
          'lorieGateATelemetryPublished' in trace, checks)
    check('counters use published shared enable',
          'lorieGateATelemetryPublished' in counter
          and 'getenv' not in counter, checks)
    check('X still has exact-string request helper',
          'lorieGateATelemetryRequested' in h
          and 'TERMUX_X11_GATEA_TELEMETRY' in h, checks)
    check('telemetry reserved is the published enable word',
          'gateATelemetry.reserved' in h
          and 'lorieGateATelemetryPublished' in h, checks)

    for stage in (
            'VALIDATE_ENTER', 'TUPLE_MATCH', 'TUPLE_MISMATCH',
            'EGL_DISPLAY_PRESENT', 'EGL_NO_DISPLAY',
            'EGL_CONTEXT_PRESENT', 'EGL_NO_CONTEXT',
            'NATIVE_CLIENT_BUFFER_CAPABLE',
            'CLIENT_BUFFER_ENTER', 'CLIENT_BUFFER_RETURN',
            'CREATE_IMAGE_ENTER', 'CREATE_IMAGE_RETURN',
            'TEXTURE_CREATE_RETURN',
            'IMAGE_TARGET_ENTER', 'IMAGE_TARGET_RETURN',
            'GL_ERROR',
            'READY_SEND_ENTER', 'READY_SEND_RETURN',
            'FAILED_SEND_ENTER', 'FAILED_SEND_RETURN',
            'VALIDATE_TERMINAL_READY',
            'VALIDATE_TERMINAL_FAILED',
            'VALIDATE_TERMINAL_FATAL'):
        check(f'stage {stage}', f'"{stage}"' in r, checks)

    check('GATEA_VALIDATE log tag exists', 'GATEA_VALIDATE' in r, checks)
    check('queue ABI remains 168', 'sizeof(LorieGpuCopyEntry) == 168' in h, checks)
    check('P0 sideband remains 40', 'sizeof(struct LorieGateAProtocol) == 40' in h, checks)

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(('PASS ' if ok else 'FAIL ') + name)
    print(f'SUMMARY total={len(checks)} failed={len(failed)}')
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT_DEFAULT)
    args = parser.parse_args()
    root = args.root
    h = (root / 'lorie.h').read_text()
    r = (root / 'renderer.cpp').read_text()
    x = (root / 'InitOutput.c').read_text()
    return verify(h, r, x)


if __name__ == '__main__':
    sys.exit(main())
