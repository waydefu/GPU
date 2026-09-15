# GATE P2-A.2 — Observe-only diagnostic rebuild

> 歷史 gate 證據。本文的 PID、APK 與觀測結果只描述 A.2 執行時狀態；P2-A 已由 A.3/A.4 關閉，目前 runtime 與下一步以 `HANDOFF.md` 為準。

```
P2-A.2: INCONCLUSIVE          CLOSED
A: ELIMINATED
B: NOT SUPPORTED
C: NOT SUPPORTED
D: NOT ESTABLISHED
Observed:
PrepareAccess succeeds.
devPrivate.ptr becomes non-NULL.
1×1 DEST devKind=4 is internally consistent.
Final observed PrepareAccess is MASK index=2, 16×16 bpp=1, devKind=64.
SIGSEGV occurs after that Prepare and before create_bits_picture.
Sfb count=0.
No 1×1 SRC index=1 Prepare observed.
No shared-buffer send observed.
damageComposite unwind repetition: LOCATION CLUE ONLY. Recursion NOT CONFIRMED.
Repair gate: CLOSED.
Next: P2-A.3 D0–D3 + E0/E1 + ucontext.
```

**Verdict: INCONCLUSIVE** — Sprep exists and **rules out A**; Sfb never fired, so A/B/C/D cannot be closed for the crashing Composite’s fb/pixman bits.

One question: *In Render Composite, before fb/pixman, at which layer does the first bad pointer/pitch state appear?*

**Observed:** no bad pointer/pitch at PrepareAccess. Crash is **after** the last Sprep and **before** `create_bits_picture` / Sfb. Unwind recovers repeating `damageComposite`, not pixman.

**Code-fix discussion is not allowed.** The unlock condition was Sprep **and** an fb-entry snapshot. Sfb count is 0. Do not change `sys_ptr` / `PixmapIsOffscreen` / PrepareAccess / GPU Composite from this gate.

P2-A.1 remains closed (B: SIGSEGV code 2 / SEGV_ACCERR / native stack unavailable). Historical Stable `:1` 512-frame overflow is still **not** Composite evidence for Stable. This experimental trial has its own unwind (below).

---

## Safety

- Stable `:1` PID **26474** `termux-x11 com.termux.x11 :1 -legacy-drawing` — alive before install, after `:3` start, after 1×1 crash, and at write-up. Package still `1.03.01-11b82d9-06.09.26`.
- Experimental only: `com.waydefu.x11gpu` `1.03.01-9449b8e-07.09.26`, helper `f8-x11gpu :3`.
- Observe-only probes. No GPU Composite. No sys_ptr / TrueNoop / PrepareAccess semantic edits.
- One `p-render-last 1x1`. Crashed `:3` not restarted. No `logcat -c` of main.

---

## Build identity

| Field | Value |
|---|---|
| tree | `src/f8-ahb` branch `f8-p2-a2-diag` |
| commit | `9449b8e09176de7ce4efb91cdc10fc2f72e6b4f4` |
| CI | GitHub `waydefu/termux-x11` run **34151817722** |
| APK | `com.waydefu.x11gpu` `1.03.01-9449b8e-07.09.26` |
| SHA256 | `cacb74527656c96fe89ea0103cc1247db7ef197b3dd569c3212942753ea26bf2` |
| CmdEntryPoint | `9449b8e09176de7ce4efb91cdc10fc2f72e6b4f4` |
| GWP-ASan | `android:gwpAsanMode="always"` (`0x1` in APK) |

Instrumented files:

- `lorie/src/main/cpp/patches/xserver.patch` — `exa/exa.c` Sprep, `fb/fbpict.c` Sfb, `os/osinit.c` Ssig, `os/backtrace.c` Sbt
- `lorie/src/main/cpp/patches/dix-config.h.in` — `p2a2_emit`
- `lorie/src/main/cpp/lorie/InitOutput.c` — `p2a2InstallCrashProbe`
- experimental manifests only — GWP-ASan always
- copy: `patches/p2-a2-observe-xserver.hunks.patch`

---

## Repro

- `:3` PID **25920** ppid=1 `termux-x11gpu com.waydefu.x11gpu :3`, thread **26704**
- Client: `CHECKPOINT COMPOSITE 1x1 op=Over filter=0 onto=pixmap` then `FAIL after composite conn=1`
- `:3` died. `:1` 26474 still up.

---

## Sprep (quoted) — crashing 1×1 pixmaps

Both 1×1 PrepareAccess calls are **index=0** (DEST). There is **no** 1×1 `index=1` (SRC) line. Last Sprep before Ssig is a 16×16 bpp=1 **index=2** (MASK).

```
Sprep-pre pix=0xb4000075be816810 index=0 has_gpu_copy=1 fb_ptr=0x0 sys_ptr=0x0 sys_pitch=4 fb_pitch=4
  dev_ptr_before=0x0 devKind_before=4 width=1 height=1 bpp=32
Sprep pix=0xb4000075be816810 index=0 has_gpu_copy=1 fb_ptr=0x0 sys_ptr=0x0 sys_pitch=4 fb_pitch=4
  dev_ptr_before=0x0 devKind_before=4 PrepareAccess_called=1 PrepareAccess_ret=1
  dev_ptr_after=0xb4000076ce82fad0 devKind_after=4 width=1 height=1 bpp=32 nested=0 skip=none ret=1

Sprep-pre pix=0xb4000075be8199f0 index=0 has_gpu_copy=1 fb_ptr=0x0 sys_ptr=0x0 sys_pitch=4 fb_pitch=4
  dev_ptr_before=0x0 devKind_before=4 width=1 height=1 bpp=32
Sprep pix=0xb4000075be8199f0 index=0 has_gpu_copy=1 fb_ptr=0x0 sys_ptr=0x0 sys_pitch=4 fb_pitch=4
  dev_ptr_before=0x0 devKind_before=4 PrepareAccess_called=1 PrepareAccess_ret=1
  dev_ptr_after=0xb4000076ce82fc50 devKind_after=4 width=1 height=1 bpp=32 nested=0 skip=none ret=1

Sprep pix=0xb4000075be817290 index=2 has_gpu_copy=1 fb_ptr=0x0 sys_ptr=0x0 sys_pitch=64 fb_pitch=64
  PrepareAccess_called=1 PrepareAccess_ret=1
  dev_ptr_after=0xb40000772e82b3c0 devKind_after=64 width=16 height=16 bpp=1 nested=0 skip=none ret=1
Ssig signo=11 code=2 addr=0x74e031bff8 (rt_sigaction)
```

Root pixmap contrast (not the 1×1 dest): `width=1280 height=1024 bpp=32` `dev_ptr_after=0x74d4ba8000` `devKind_after=5120`.

Always on these 1×1 lines: `has_gpu_copy=1`, `fb_ptr=0x0`, `sys_ptr=0x0`, hook `called=1` `ret=1`, `skip=none`.

---

## Sfb — missing (not guessed)

```
Sfb count: x11gpu-p2a2.snap=0  logcat-live.txt=0
```

No `Sfb role=src|mask|dst` line. Crash is after last Sprep, before `pixman_image_create_bits` in `create_bits_picture`. That is a **negative** fb-entry result, not a bits/devKind snapshot.

This trial also has **zero** `Sent shared buffer` lines in `logcat-live.txt`. P2-A.1’s 1×1 had `width 1 stride 64`. Historical AHB stride 64 is **not** evidence for this flight’s 1×1 pitch.

---

## Letter rules applied (strict)

| Letter | Rule | This flight |
|---|---|---|
| **A** | `PrepareAccess_called=0` for the pixmap fb would use | **Ruled out.** Both 1×1 DEST prepares have `called=1`. |
| **B** | called=1 but `dev_ptr_after` NULL or known-stale/sys_ptr | **Not met.** After-hook ptrs are non-NULL (`0xb4000076ce82fad0`, `0xb4000076ce82fc50`) and are **not** `sys_ptr` (`sys_ptr=0`). Heap-tagged `0xb40000…` vs root AHB `0x74d4…` is a mapping *class* difference, not a proven stale pointer. |
| **C** | ptr plausible but `devKind` / rowstride disagree with width/bpp or AHB stride | **Not met on this flight.** `devKind_after=4` matches 1×1×32bpp. No Sfb `rowstride_bytes`. No this-trial AHB stride 64. |
| **D** | ptr+pitch coherent; fault in pixman / FinishAccess / lifetime | **Not assignable.** Pitch is internally coherent, but Sfb never ran and unwind is not pixman. |

**INCONCLUSIVE** is the letter. Closest Sprep-only reading is “not A/B/C”; that is not D.

---

## libunwind / GWP-ASan / crash buffer

**Ssig** (kernel `rt_sigaction` handler, not `OsSigHandler` “Caught signal”):

```
Ssig signo=11 code=2 addr=0x74e031bff8 (rt_sigaction)
```

Same class as P2-A.1 (`code 2`, fault `…ff8`). Handler then `_exit`, so debuggerd/crash_dump did not add a new tombstone. `logcat -b crash` still shows P2-A.1 PID **19128** only.

**First unwind frame printed: yes.**

```
Sbt 0: .../libXlorie.so (xorg_backtrace+0x48)
Sbt 1: .../libXlorie.so (?+0xe7efc)          → p2a2CrashHandler InitOutput.c:158
Sbt 2: ? (?+0x0) [0x77f8fc1874]            → trampoline
Sbt 3: ... (?+0x27e234)                    → damageComposite damage.c:513
Sbt 4+: ... (?+0x27e248) × 60               → damageComposite damage.c:518
```

CI unstripped `libXlorie.so` (run 34151817722): see `sbt-addr2line.txt`.

`_Unwind_Backtrace` ran from the alt-stack handler **without ucontext**. Sbt 0–1 are handler frames. Sbt 3+ are recovered interrupted-stack frames. Two distinct `damageComposite` PCs (513 once, then 518 repeating) is not a single-PC unwind loop. No `fbComposite` / `create_bits_picture` / `pixman_*` / `ExaDoPrepareAccess` / `loriePrepareAccess` names in Sbt.

Meson `option libunwind`: **not enabled** (`HAVE_LIBUNWIND` still `#undef` in `dix-config.h.in`). Android Sbt uses `_Unwind_Backtrace` anyway; it did emit frames.

**GWP-ASan:** manifest always; **no** GWP abort / report in grepped logcat. Miss **does not** exclude heap overflow.

---

## What is missing (do not invent)

1. **Sfb** — `create_bits_picture` never logged; no `bits` / `rowstride_bytes` for src/mask/dst.
2. **1×1 SRC PrepareAccess** (`index=1`) — absent.
3. **This-trial AHB describe** — no `Sent shared buffer width 1 stride 64`.
4. **OsSigHandler “Caught signal”** — SIGSEGV taken by `p2a2CrashHandler` first.
5. **ucontext unwind / debuggerd `#00 pc`** — still none; crash buffer unchanged.
6. **GWP-ASan hit** — none (miss ≠ exclude).

---

## `:1` untouched

Confirmed in `repro-run.txt` (PRE / POST_ACTIVITY / POST_X3 / POST_REPRO) and at write-up: PID **26474** still `termux-x11 com.termux.x11 :1 -legacy-drawing`. Experimental APK `applicationId` is `com.waydefu.x11gpu`.
