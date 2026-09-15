# Gate A P2 R1 diagnostic handler — local compile 2026-09-14

Diagnostic-only. No Gate A semantics, queue ABI, sideband ABI, B1–B4,
lifecycle, or probe hot-path change.

## SOURCE

Worktree: `/root/projects/GPU加速/src/f8-ahb-gatea-a1`
Branch: `qualification/gatea-a1-microprobe-20260912`
Base: `15caa00908aa9d1f1c4a78bb630aa24a93e7e4cd`
Commit: `dd81ac056bd3fe84d757c63c5ee484a2037ebb4f`
`chore(gatea): capture raw crash ucontext`

File: `lorie/src/main/cpp/lorie/InitOutput.c` only (+48/−1).

`p2a3CrashHandler` keeps the existing `Uctx` parse, then:

- `Upid pid=` via `getpid()` and `tid=` via `syscall(SYS_gettid)`
- `Uraw` 64 little-endian qwords (first 512 bytes of `ucontext_t`)
- stack buffers + `write` only (`p2a3WriteLine` / `p2a3PutHex64`)
- `xorg_backtrace()` remains unsafe auxiliary, not original-PC authority

## NATIVE COMPILE

`:lorie:buildCMakeDebug[arm64-v8a]`, `--no-daemon --no-build-cache`,
`LANG=C.UTF-8`.

1. `git diff --check`: PASS (exit 0).
2. Incremental: BUILD SUCCESSFUL in 25s, exit 0.
   Log: `GATE-A-P2-R1-DIAG-NATIVE-BUILD-20260914.log`.
3. Full clean (`:lorie:clean` then the same native task): BUILD SUCCESSFUL
   in 2m 52s, exit 0.
   Log: `GATE-A-P2-R1-DIAG-NATIVE-BUILD-FULL-20260914.log`.
4. Warnings: 41 C/C++ warnings, identical `(file, -Wtype, message)`
   fingerprint set to B1–B4 full-clean baseline
   (`GATE-A-P2-B1-B4-NATIVE-BUILD-FULL-20260914.log`). NEW unique: 0.

## SELF-REVIEW

- Root cause of PID 31807 SIGSEGV: NOT claimed; this only captures context.
- Fail-stop: unchanged (`_exit(128+signo)`).
- No fallback/retry, no ownership/ABI change, default-OFF unchanged.
- Cleanup of handler resources unchanged (`p2a3SnapFd` still append-only).

## SCOPE

No ADB / install / `:3` / display 0 / R1–R10 device cells in this compile
step. Production Gate A unchanged / BLOCKED.
