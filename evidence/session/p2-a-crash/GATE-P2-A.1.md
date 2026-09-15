# GATE P2-A.1 — Crash buffer capture

> 歷史 gate 證據。本文的 PID、APK 與 next-gate 只描述 A.1 執行時狀態；P2-A 已由 A.3/A.4 關閉，目前 runtime 與下一步以 `HANDOFF.md` 為準。

**Verdict: B** — relevant experimental `:3` crash exists, but the stack is insufficient (no `#00 pc` / module / BuildId).

Historical buffer was **C** (no `:3` records). One documented 1×1 Composite repro was then run on experimental `:3` only. Fresh crash buffer has SIGSEGV/SEGV_ACCERR + fault address, then `crash_dump` died before a native backtrace.

Do **not** rebuild APK/Xorg for symbolication of this dump. Next gate: **P2-A.2 diagnostic rebuild (observe-only)**. Do not start P2STAGE in this gate.

Stable `:1` was **not touched** (PID **26474** `termux-x11 com.termux.x11 :1 -legacy-drawing` alive before and after; no install / force-stop / restart / Display2 restore).

---

## Safety

- adb serial `10.129.215.219:35859` (also attached as `127.0.0.1:35859`; all commands used `-s 10.129.215.219:35859`)
- Experimental package `com.waydefu.x11gpu` `1.03.01-a401b4f-07.09.26` (CmdEntryPoint `a401b4fb1f5d640aca68ee0b84b437ca95f6d519`)
- No APK/Xorg rebuild. No code change. No xfwm. No P2STAGE. Crashed `:3` instance was **not** restarted.

## Historical `logcat -b crash -d` (C for `:3`)

No `waydefu` / `x11gpu` / `:3` / `termux-x11gpu` lines.

Records present:

| Time | Process | Class |
|---|---|---|
| 01-04 08:24:39 | `init` | SIGABRT, unrelated |
| 09-07 21:44:42 | `termux-x11 com.termux.x11 :1 -legacy-drawing` | SIGSEGV SEGV_ACCERR, **stack overflow**, 512 recursive `libXlorie.so` frames |
| 09-07 21:49:40 | `termux-x11 com.termux.x11 :1` | same Stable `:1` stack overflow |
| 09-07 21:52:34 | `termux-x11 com.termux.x11 :1 -legacy-drawing` | same |
| 09-07 22:34:09 | `adbd` | SIGABRT, unrelated |

Those `:1` tombstones **are not** the P2 Composite crash. debuggerd *did* unwind them because they were a 512-frame stack overflow in **Stable** `com.termux.x11` (`BuildId: 3009169992ff7909c19f4c8c846d20c7053d208a`, `#00 pc 000000000027c100` repeating). Frame names `ExaDoPrepareAccess` / `create_bits_picture` / `fbComposite` / `pixman_image_composite` / `loriePrepareAccess` do **not** appear.

Excerpt (historical, **not relevant**):

```
09-07 21:44:42.509 25700 25724 F libc    : Fatal signal 11 (SIGSEGV), code 2 (SEGV_ACCERR), fault addr 0x71e9b15ff8 in tid 25724 (main), pid 25700 (main)
09-07 21:44:42.672 26573 26573 F DEBUG   : Cmdline: termux-x11 com.termux.x11 :1 -legacy-drawing
09-07 21:44:42.672 26573 26573 F DEBUG   : signal 11 (SIGSEGV), code 2 (SEGV_ACCERR), fault addr 0x00000071e9b15ff8
09-07 21:44:42.672 26573 26573 F DEBUG   : Cause: stack pointer is not in a rw map; likely due to stack overflow.
09-07 21:44:42.672 26573 26573 F DEBUG   : 512 total frames
09-07 21:44:42.672 26573 26573 F DEBUG   :       #00 pc 000000000027c100  .../com.termux.x11-.../base.apk!libXlorie.so (offset 0xd8000) (BuildId: 3009169992ff7909...)
09-07 21:44:42.672 26573 26573 F DEBUG   :       #01 pc 000000000027c110  .../com.termux.x11-.../base.apk!libXlorie.so ...
```

## C-path: one 1×1 repro on `:3`

Because historical was C: `adb logcat -b crash -c` (crash buffer only), then documented client `patches/p_render_last.c` mode `1x1` on a double-fork `f8-x11gpu :3` (no xfwm).

- X PID **19128** ppid=1, thread `main` **19156**
- Tester: `CHECKPOINT COMPOSITE 1x1 op=Over filter=0 onto=pixmap` then `FAIL after composite conn=1`
- `:3` died; `:1` 26474 still up

### Crash buffer after repro (entire dump)

```
--------- beginning of crash
09-08 01:51:50.687 19128 19156 F libc    : Fatal signal 11 (SIGSEGV), code 2 (SEGV_ACCERR), fault addr 0x7b498b5ff8 in tid 19156 (main), pid 19128 (main)
09-08 01:51:50.797 19128 19156 F libc    : Crash due to signal: crash_dump helper failed to exec, or was killed
```

No `#00 pc`, no module, no BuildId, no Abort message, no named frames.

### Main buffer (same event; debuggerd lost the race)

```
09-08 01:51:48.682 19128 I CmdEntryPoint: commit a401b4fb1f5d640aca68ee0b84b437ca95f6d519
09-08 01:51:49.267 19128 19156 I LorieNative: flight recorder installed path=/tmp/x11gpu-flight.ring cap=256
09-08 01:51:50.681 19128 19156 I LorieNative: Sent shared buffer width 1 stride 64 height 1 format 2 type 3 id 18
09-08 01:51:50.684 19128 19156 I LorieNative: Sent shared buffer width 1 stride 64 height 1 format 2 type 3 id 19
09-08 01:51:50.686 19128 19156 I libc    : handling signal: 11
09-08 01:51:50.687 19128 19156 F libc    : Fatal signal 11 (SIGSEGV), code 2 (SEGV_ACCERR), fault addr 0x7b498b5ff8 in tid 19156 (main), pid 19128 (main)
09-08 01:51:50.687 19128 19156 I libc    : debuggerd_dispatch_pseudothread start. crashing tid: 19156
09-08 01:51:50.735 19128 19156 I libc    : crash_dump pid: 19215
09-08 01:51:50.769 19215 I crash_dump64: crash_dump start
09-08 01:51:50.785 19216 W crash_dump64: failed to attach to thread 19128: No such process
09-08 01:51:50.795 19216 F crash_dump64: crash_dump.cpp:805] failed to attach to thread 19156: No such process
09-08 01:51:50.796 19216 E libc    : failed to connect to tombstoned: Permission denied
09-08 01:51:50.797 19128 19156 F libc    : Crash due to signal: crash_dump helper failed to exec, or was killed
```

Same signature as `evidence/session/flight/repro-1x1-logcat.txt` (PID 14011): 1×1 AHB export → SIGSEGV SEGV_ACCERR at `…ff8` → crash_dump cannot ptrace → tombstoned permission denied. Process name in GLES init: `termux-x11gpu com.waydefu.x11gpu :3`.

## Priority evidence (fresh `:3`)

| Field | Result |
|---|---|
| native backtrace `#00 pc` | **absent** |
| faulting module | **unknown** (crash_dump never attached) |
| SIGSEGV / SEGV_ACCERR | **yes** (code 2) |
| fault address | `0x7b498b5ff8` |
| thread / PID | tid **19156** (`main`), pid **19128** (`termux-x11gpu com.waydefu.x11gpu :3`) |
| BuildId | **absent** |
| named frames (`ExaDoPrepareAccess`, `create_bits_picture`, `fbComposite`, `pixman_image_composite`, `loriePrepareAccess`) | **none** |
| symbolication | **not attempted** — no PC/rel_pc/mapping |

## Recommended next gate

**P2-A.2 diagnostic rebuild (observe-only).** This dump cannot be symbolicated. A usable unwind needs libunwind / `Caught signal` in logcat and/or a crash_dump that can attach (process is gone in ~110 ms). Do not start P2STAGE instrumentation in P2-A.1. Do not change `sys_ptr` / `PixmapIsOffscreen` / `PrepareAccess` / GPU Composite from this evidence alone.
