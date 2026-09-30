# PROOT kompat-lean — upstream PR DRAFT (NOT SUBMITTED)

Status: draft only. Not sent to any upstream. Sending needs explicit authorization.
Source evidence: `PROOT-KOMPAT-OVERHEAD-01.md` (primary). Patch tree: `~/build/proot-fast/proot-5.1.107.92-v2` (workstation only; the diff is NOT in this repo — export with `diff -u` against stock `proot-5.1.107.92` before submitting).
Scope: v2 kompat-lean only. Do NOT include v5/v6 stat/statx fast-paths (separate redesign; separate PR later).

## Title
kompat: don't seccomp-trap syscalls whose handlers are no-ops on the running kernel

## Problem
When `--kernel-release` is given (proot-distro always does, to fake `uname`), the kompat extension
loads `filtered_sysnums[]` (33 syscalls incl. `futex`, `epoll_pwait`, `pselect6`, `fcntl`, `pipe2`,
`dup3`, `eventfd2`, `accept4`, `socket`, `openat` and `execve` with FILTER_SYSEXIT) unconditionally.
Every handler is gated by `needs_kompat(config, KERNEL_VERSION(2,6,x))`, max threshold 2.6.29. On any
modern kernel they all return immediately, but each call was already ptrace-stopped (twice for
FILTER_SYSEXIT entries). ptrace-stop sampling of a real session: recvmsg 39.7%, futex 28.1%,
epoll_pwait 20.7%.

## Change
If the real kernel is >= 2.6.29 and `PROOT_KOMPAT_FULL` is unset, kompat filters only
`uname`/`sethostname`/`setdomainname` (fake-version behaviour unchanged).
`PROOT_KOMPAT_FULL=1` or `PROOT_FORCE_KOMPAT` restores the previous behaviour; old kernels unchanged.

## Evidence (POCO F8 Ultra, Android 16, kernel 6.17, stock vs patched, same binary otherwise)
| µs | stock | patched | patched + PROOT_KOMPAT_FULL=1 |
|---|---|---|---|
| futex_wake | 31.6 | 0.23 | 29.4 |
| epoll_pwait(0) | 31.9 | 0.21 | 33.5 |
| fcntl(GETFL) | 63.5 | 0.22 | 66.4 |
| open+close | 128.5 | 82.9 | 127.1 |

Agent-style mix (git/grep/find/python/node/bash, 10 each): wall 15.6 s -> 7.3 s (-53%),
CPU 16.3 s -> 7.5 s (-54%); with `PROOT_KOMPAT_FULL=1` back to 18.4 s (red control).
Functional smoke (root id, chmod/chown, hardlink/symlink, Python threads, sqlite, ssl, Node
worker/child_process, git, dpkg, DNS, SysV IPC): stock vs patched output byte-identical.

## Decisions (2026-09-30, user-confirmed plan)
- Target: `termux/proot` first (all patch/build/smoke/bench data is on its 5.1.107.92 + proot-distro). Both
  `proot-me/proot` and `termux/proot` `kompat.c` share the fixed `filtered_sysnums[]` + `needs_kompat()` design, so
  the core can be re-cut as a generic patch for proot-me later if maintainers prefer.
- Commit A = filter reduction only. vDSO (`AT_SYSINFO_EHDR`) change is OUT of PR #1 (separate commit/PR, own justification).
- Required before submit: (1) export v2 diff on workstation and strip vDSO hunk; (2) pure-ptrace fallback correctness test
  (seccomp unavailable: no crash / no regression); (3) **re-run benchmarks on the vDSO-free build** — the tables below were
  measured WITH vDSO kept, so `clock_gettime`, and possibly open+close and AGENT-MIX, will change; (4) report both runs or median/range.
- Then rewrite the English PR text from the real diff. Suggested one-line thesis:
  "Do not install compatibility syscall filters for kernel features that the actual host kernel already provides."

## Review risks to resolve BEFORE submitting
1. **vDSO**: the v2 patch also stops stripping `AT_SYSINFO_EHDR` (gives `clock_gettime` 0.22 -> 0.06 µs).
   Stock strips it so programs can't read the real kernel version from the vDSO. This is a
   behaviour change, not a pure "avoid needless traps" change. Either split it into a second
   commit/PR with its own justification, or keep it behind the same gate and state the trade-off
   explicitly. Recommend: separate commit.
2. **Seccomp-absent path**: confirm behaviour when seccomp is unavailable (ptrace-only fallback)
   is unchanged; evidence file does not cover it.
3. **Other kernels/devices**: all numbers are one device. Ask reviewers/others to reproduce, or
   add a second device before claiming general benefit.
4. **Target repo**: decide whether this goes to proot-me/proot or Termux's proot fork
   (proot-distro uses the latter's lineage); check for existing kompat issues/PRs first.
5. Numbers are first-run of two; raw files hold the second run.

## Not included
v5/v6 stat/statx enter-path fast-paths, v1 socket/clone rules.
