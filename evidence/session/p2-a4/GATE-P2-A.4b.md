# GATE P2-A.4b — histogram probe correctness + Damage return

> 歷史 gate 證據。本文的 PID、APK 與觀測窗口只描述 A.4b；P2-A 已關閉，目前 runtime 以 `HANDOFF.md` 為準。

```
P2-A.4b: PASS
probe_enter_count = 1
probe_return_count = 1
max_probe_depth = 1
xrender_ops = 1
hist[0] count = 1  (not double-counted)
SRC present / MASK none / DEST present  — correct for 1×1 Over→Src
D3 = 1  (Damage returned)
1×1 Composite: SURVIVED (still alive at A.4b)
X :3 PID 32075 ppid=1  xdpyinfo ok
Stable :1 PID 26474 untouched
Implication (context only):
P2 crash root cause was instrumentation hook corruption, not backing/pitch.
Next gate: A.4c
```

A.4a remains **PASS** (install-once topology). This gate only checks that the observe-only histogram probe records one Composite correctly and that Damage returns. **No extra 1×1 / SRC / 16×16 MASK matrix** — the A.4a 1×1 is SRC+DEST, not DEST-only, so SRC/MASK/DEST can be judged from that one request.

Did **not** restart `:3`, did **not** re-run `p-render-last` (existing stamps + 5s FPS dump are sufficient), did **not** start XFCE / xfwm, did **not** reopen pixmap/EXA/fb/pixman/sys_ptr as a crash campaign. No InitOutput stamp added. No commit.

---

## Safety

- Stable `:1` PID **26474** `termux-x11 com.termux.x11 :1 -legacy-drawing` — alive at A.4a close and at A.4b write-up (`2026-09-08T04:25:04+08:00`, elapsed ~05:28:54).
- Experimental only: `com.waydefu.x11gpu` `1.03.01-6182b94-07.09.26` on `:3` PID **32075** ppid=1 (same instance as A.4a). `xdpyinfo :3` ok.
- No xfwm / XFCE. No `sys_ptr` / pitch / Damage-bypass / `if (depth > N) return` / SIGILL special-case / force software. Histogram probe left on.

---

## Method

Existing A.4a 1×1 flight on PID 32075 (`DISPLAY=:3 /tmp/p-render-last 1x1`, tester_rc=0). Histogram is dumped by `lorieFramecounter` in `InitOutput.c` every 5s as `xrender_ops=` plus `xrender hist[n] count=… op=… src=… mask=… dst=… flags=… wbucket=… last=…`, then counters are zeroed. That dump is in `logcat-live.txt` / `a4b-hist-dump.txt`, not in `p2a2_emit` stamps.

---

## Criteria

| # | Check | Result |
|---|---|---|
| 1 | `probe_enter_count == probe_return_count` | **1 = 1** |
| 2 | `max_probe_depth == 1` | **1** (`Probe ENTER depth=1 max=1`) |
| 3 | histogram still increases | **`xrender_ops=1`** then `hist[0] count=1` at 04:11:58 (same 5s window as the 04:11:51 Composite) |
| 4 | one Composite not double-counted | enter=1, return=1, `xrender_ops=1`, hist slot count=1, one D0, one E0, one D3 |
| 5 | SRC / MASK / DEST classification | **SRC+DEST, MASK none** — see below |
| 6 | probe does not mutate Picture/Drawable | same `pSrc`/`pMask`/`pDst`/`srcDraw`/`dstDraw` D0 → E0 → E0u; probe only `xrenderHistRecord` then `saved(...)` with the same pointers |
| 7 | call-through exactly once | one ENTER, one `saved()` = `exaComposite` (E0), one RETURN |
| 8 | Damage returns | **D3 = 1**, X still alive |
| 9 | no stack growth | depth stays **1** (A.3 was 1029 / D3=0) |
| 10 | no new SIGILL / SIGSEGV | **Ssig/Uctx/Fatal = 0**; `:3` still PID 32075 |

---

## Histogram (5s FPS dump)

```
04:11:51.507  D0 / Probe ENTER  (the 1×1)
04:11:51.519  Probe RETURN / D3
04:11:58.156  xrender_ops=1
04:11:58.156  xrender hist[0] count=1 op=1 src=20020888 mask=00000000 dst=20020888 flags=0x0 filter=0 wbucket=0 last=1x1
04:13:11.831  xrender_ops=0   (next window after reset; no extra Composite)
```

`xrenderOps++` is once per `lorieCompositeProbe` entry (`xrenderHistRecord`). Matching enter=1 and `xrender_ops=1` means the probe is not counting the inner `exaComposite`/`fbComposite` as a second op.

Flag bits (InitOutput.c): bit0=mask present, bit1=src transform, bit2=src CA, bit3=mask CA, bit4=src repeat, bit5=mask repeat.

---

## SRC / MASK / DEST (this 1×1, not DEST-only)

Client: `p-render-last 1x1` = PictOpOver, mask=`XCB_NONE`, 1×1 pixmap src + 1×1 pixmap dest.

Server `ReduceCompositeOp` turns opaque-src Over into **PictOpSrc (1)** before `damageComposite`. `srcFmt=20020888` is `PICT_x8r8g8b8` (A=0), so that reduction is expected. Probe records the post-reduce op.

| Role | Probe / hist | PrepareAccess in the ENTER→RETURN window |
|---|---|---|
| **SRC** | `pSrc≠0`, `src=20020888`, `srcDraw=0xb40000769b0154f0`, Sfb `role=src` | `index=1` 1×1 bpp=32 pix=`…154f0` |
| **MASK** | `pMask=0`, `mask=00000000`, `flags=0x0` (bit0 clear), `mask_kind=-1` | **no** `index=2` on this Composite |
| **DEST** | `pDst≠0`, `dst=20020888`, `dstDraw=0xb40000769b014fb0`, Sfb `role=dst` | `index=0` 1×1 bpp=32 pix=`…14fb0` |

16×16 bpp=1 `index=2` MASK `Sprep` lines exist **outside** this Composite (glyph/cursor around map/RandR). They do **not** go through the histogram probe (`hist` mask=0, `xrender_ops=1` only). Optional extra cases were **not** run.

Pointer identity (observe-only, no picture “fix”):

```
D0   pSrc=0xb40000762b029000 pMask=0x0 pDst=0xb40000762b0285e0
     srcDraw=0xb40000769b0154f0  dstDraw=0xb40000769b014fb0
E0   same four pointers, xywh=0,0,1,1
E0u  same; srcPix=srcDraw, dstPix=dstDraw, maskPix=0
Sfb  pix matches srcDraw / dstDraw
```

Call-through: `damageComposite` unwrap → `lorieCompositeProbe` → `exaComposite` (E0/E0u) → `fbComposite` (E1) → RETURN → D3.

---

## Stamp counts (same 1×1 as A.4a)

| Stamp | Count |
|---|---|
| D0 / D1 / D2 | 1, depth 1 |
| Probe ENTER / RETURN | **1 / 1**, max_depth=1 |
| E0 / E0u / E1 / Sfb | 1 / 1 / 2 / 2 (E0/E1/Sfb noted for **A.4c**, not diagnosed here) |
| D3 | **1** |
| xrender_ops / hist count | **1 / 1** |
| Ssig / Uctx | **0** |

---

## Live at write-up

| | |
|---|---|
| `:1` | PID **26474** ppid=4718 `termux-x11 com.termux.x11 :1 -legacy-drawing` |
| `:3` | PID **32075** ppid=1 `termux-x11gpu com.waydefu.x11gpu :3` (~13 min up, same as A.4a) |
| APK | `com.waydefu.x11gpu` `1.03.01-6182b94-07.09.26` SHA256 `9f2f8651378c3bbd3cbccff0566538d64af7cf22e349c874c470d848935cd42b` |
| commit | `6182b94bc69166e49a2f6ca0238ffdba9781fc68` CI **34157648272** |

---

## Verdict

**PASS.** Probe enter/return match, depth stays 1, histogram increments by exactly one for one 1×1, SRC/MASK/DEST match that request, pictures are not mutated by the probe, Damage returns, X `:3` still alive, `:1` still 26474. No code change.

**P2 crash root cause was instrumentation hook corruption, not backing/pitch.**

E0/E0u/E1/Sfb fired on this surviving 1×1 — record for **A.4c** as path observation only. Do not start a backing/pitch crash campaign. Do not start XFCE until A.4c is accepted.

Next gate: **A.4c** (E0/E1/Sfb path observation).
