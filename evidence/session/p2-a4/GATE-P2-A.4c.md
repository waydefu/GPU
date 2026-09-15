# GATE P2-A.4c — Composite → Damage → probe → EXA/unaccel → fb/pixman path

> 歷史 gate 證據。本文的 PID、APK 與觀測窗口只描述 A.4c；P2-A 已關閉，目前 runtime 以 `HANDOFF.md` 為準。

```
P2-A.4c: PASS
Path observed (same A.4a 1×1, not re-run):
E0 = 1
E0u = 1
E1 = 2  (PRE_SWAP + PRE_FB_COMPOSITE)
Sfb = 2  (role=src + role=dst)
Sprep in E0u→E1 window = 2  (dst index=0, src index=1; both ret=1)
Sbt = 0
Probe ENTER / RETURN = 1 / 1
D3 = 1
fb/pixman: REACHED and COMPLETED (Sfb then RETURN then D3)
1×1 Composite: SURVIVED
X :3 PID 32075 ppid=1  xdpyinfo ok (still alive at A.4c write-up)
Stable :1 PID 26474 untouched
Classification:
fb/pixman was reached and survived.
Original P2 crash was hook corruption; backing/pitch remains
not implicated for this 1×1.
Next gate: Gate 4 / P2-A.4d regression
```

A.4a remains **PASS** (install-once topology). A.4b remains **PASS** (histogram probe + Damage return). This gate only records that the surviving 1×1 actually walked EXA unaccel into `fbComposite` / pixman `create_bits_picture` and **returned**. **No extra 1×1 / SRC / 16×16 MASK matrix.** Did **not** re-run `p-render-last` (E0/E0u/E1/Sfb already complete in `stamps.txt` / `logcat-key.txt` / `x3-stdout.log`). Did **not** start XFCE / xfwm. Did **not** implement any sys_ptr / pitch / PrepareAccess “fix”. A.2 / A.3 stay sealed.

---

## Safety

- Stable `:1` PID **26474** `termux-x11 com.termux.x11 :1 -legacy-drawing` — alive at A.4a, A.4b (`2026-09-08T04:25:04+08:00`), and A.4c (`2026-09-08T04:27:54+08:00`, elapsed ~05:31:45). DISPLAY `:1` was not queried.
- Experimental only: `com.waydefu.x11gpu` `1.03.01-6182b94-07.09.26` on `:3` PID **32075** ppid=1 (same instance as A.4a/A.4b). `xdpyinfo :3` ok at write-up.
- No xfwm / XFCE. No `sys_ptr` / pitch / Damage-bypass / `if (depth > N) return` / SIGILL special-case / force software. Histogram probe left on. No commit / push / CI.

---

## Method

Existing A.4a 1×1 flight on PID 32075 (`DISPLAY=:3 /tmp/p-render-last 1x1`, tester_rc=0, `RESULT render-last PASS mode=1x1 X alive` at 04:11:51). Stamps extracted from:

| File | Role |
|---|---|
| `stamps.txt` / `logcat-key.txt` | E0/E0u/E1/Sfb/Probe/D3 counts |
| `x3-stdout.log` / `x11gpu-p2a3.snap` | Sprep in the E0u→E1 window; D1/D2 |
| `logcat-live.txt` | timestamps (D0 04:11:51.507 → D3 04:11:51.519) |
| `addr2line.txt` / `nm-hooks.txt` / `maps-libXlorie.txt` | function identity vs `libXlorie.so` r-xp base `0x7498a23000` |

A.4c live check: PID + `xdpyinfo :3` only (`a4c-live-check.txt`). Window extract: `a4c-path-window.txt`.

---

## Q1 — Did the software/fb path actually run?

**Yes.** After Damage unwrap and one probe call-through, EXA took the unaccel path and called `fbComposite`.

| Stamp | Count | What it is |
|---|---|---|
| E0 `EXA_COMPOSITE_ENTER` | **1** | `exaComposite` entered, `xywh=0,0,1,1`, `swappedOut=0` |
| E0u `EXA_UNACCEL_ENTER` | **1** | `ExaCheckComposite` / unaccel entered (not GPU Composite) |
| E1 `PRE_SWAP` | **1** | pointers/kind after PrepareAccess, about to swap to fb |
| E1 `PRE_FB_COMPOSITE` | **1** | callee = `fbComposite` |
| E1 total | **2** | same convention as A.4a/A.4b |
| Sfb `role=src` | **1** | pixman bits picture for SRC |
| Sfb `role=dst` | **1** | pixman bits picture for DEST |
| Sfb total | **2** | MASK none → no Sfb mask |
| Sprep in E0u→E1 | **2** | DEST `index=0` then SRC `index=1`; both `PrepareAccess_ret=1` |
| Sbt | **0** | crash backtrace stamp; none (A.2 used Sbt on SIGSEGV) |

A.3 on the cycling build had **E0/E0u/E1/Sfb = 0** (EXA/fb never reached). This flight is the opposite.

---

## Q2 — Did those stamps return (not die mid-fb)?

**Yes.** Order on one thread (32075/32460), ~12 ms:

```
D0 → D1 → D2 → Probe ENTER
  → E0 → E0u
    → Sprep DEST → Sprep SRC
    → E1 PRE_SWAP → E1 PRE_FB_COMPOSITE
    → Sfb src → Sfb dst
  → Probe RETURN enter=1 return=1
→ D3 AFTER_CALL depth=1
```

Pairing:

| Enter | Return evidence |
|---|---|
| E0 / E0u | E1 + Sfb fire after them (unaccel did not abort) |
| E1 PRE_FB | Sfb src+dst then Probe RETURN (fbComposite returned) |
| Sfb | immediately followed by Probe RETURN then D3 (not a last-line-before-death) |
| Probe ENTER | Probe RETURN 1/1, max_depth=1 |
| D0 | D3 = 1 |

No Ssig / Uctx / Fatal / Sbt. Tester PASS. `:3` still PID 32075 at A.4c.

---

## Q3 — Pointer/pitch snapshot (record only; no new diagnosis)

Observed on this surviving 1×1:

| Site | SRC | DEST | MASK |
|---|---|---|---|
| D0 / E0 drawable | pix `…154f0` | pix `…14fb0` | 0 |
| E0u `*_ptr` | `0x0` kind=4 1×1×32 | `0x0` kind=4 1×1×32 | none |
| Sprep-pre | `sys_ptr=0x0` `fb_ptr=0x0` `sys_pitch=4` `fb_pitch=4` `devKind=4` | same | — |
| Sprep after | `dev_ptr_after=0xb40000761b02ac50` ret=1 | `dev_ptr_after=0xb40000761b02abb0` ret=1 | — |
| E1 PRE_SWAP | `src_ptr=0xb40000761b02ac50` kind=4 | `dst_ptr=0xb40000761b02abb0` kind=4 | 0 |
| Sfb | `bits=…2ac50` `devKind=4` `rowstride_bytes=4` `stride_words=1` | `bits=…2abb0` same pitch | — |

`devKind` / `sys_pitch` / `fb_pitch` / Sfb `rowstride_bytes` are **4** for this 1×1 bpp=32 (one pixel row). E0u `*_ptr=0` is **before** the two PrepareAccess calls; E1/Sfb see the post-PrepareAccess bits.

**Classification (required):** 1×1 completed and X is still alive → **fb/pixman was reached and survived**. Original P2 crash was hook corruption; backing/pitch remains **not implicated for this 1×1**.

Pointer/pitch diagnosis is **not reopened**. It would only reopen if this flight crashed inside E0/E1/Sfb. It did not.

---

## Q4 — Call chain (this 1×1)

`libXlorie.so` r-xp base `0x7498a23000` (`/proc/32075/maps`). Unstripped CI `34157648272`:

```
damageComposite          0x7498ca2e58  +0x27fe58  damage.c:491
  unwrap
lorieCompositeProbe      0x7498b0f35c  +0xec35c   InitOutput.c:809
  saved (not damageComposite)
exaComposite             0x7498d416e0  +0x31e6e0  exa_render.c:878     ← E0
  ExaCheckComposite      0x7498d44898  +0x321898  exa_unaccel.c:599     ← E0u
    PrepareAccess DEST/SRC                                              ← Sprep
    unwrap to fb
fbComposite              0x7498c20934  +0x1fd934  fbpict.c:50           ← E1
  create_bits_picture / pixman                                          ← Sfb src, Sfb dst
  return
Probe RETURN / D3
```

```
Composite request (PictOpOver → PictOpSrc, 1×1, MASK none)
        │
        ▼
 damageComposite          0x7498ca2e58     D0 depth=1
        │ unwrap
        ▼
 lorieCompositeProbe      0x7498b0f35c     Probe ENTER
        │ saved
        ▼
 exaComposite             0x7498d416e0     E0
        │
        ▼
 ExaCheckComposite        0x7498d44898     E0u  (software, not GPU)
        │ PrepareAccess DEST then SRC      Sprep ×2 ret=1
        ▼
 fbComposite              0x7498c20934     E1 PRE_FB
        │ pixman bits pictures             Sfb src + Sfb dst
        ▼
 Probe RETURN  (enter=1 return=1)
        ▼
 damageComposite AFTER_CALL                D3 depth=1
```

A.3 cycle `damageComposite ↔ lorieCompositeProbe` is absent: probe `saved` is `exaComposite`, depth stays 1, D3 fires, fb is reached.

---

## Live at write-up

| | |
|---|---|
| `:1` | PID **26474** ppid=4718 `termux-x11 com.termux.x11 :1 -legacy-drawing` |
| `:3` | PID **32075** ppid=1 `termux-x11gpu com.waydefu.x11gpu :3` (~16 min up, same as A.4a) |
| APK | `com.waydefu.x11gpu` `1.03.01-6182b94-07.09.26` SHA256 `9f2f8651378c3bbd3cbccff0566538d64af7cf22e349c874c470d848935cd42b` |
| stable pkg | `com.termux.x11` `1.03.01-11b82d9-06.09.26` |
| commit | `6182b94bc69166e49a2f6ca0238ffdba9781fc68` CI **34157648272** |

---

## Verdict

**PASS.** Software/fb path ran (E0=1, E0u=1, E1=2, Sfb=2), stamps returned into Probe RETURN and D3, no crash in E0/E1/Sfb, `:3` still 32075, `:1` still 26474. Path observation only; no code change.

**fb/pixman was reached and survived. Backing/pitch is not implicated for this 1×1.**

Do **not** start XFCE. Next is the A.4d regression matrix, not a desktop session.

---

## Next after A.4c PASS — Gate 4 / P2-A.4d regression

Name only; **not run in A.4c**:

```
1×1 DEST
1×1 SRC
16×16 MASK
p-render-last
原 Composite reproducer
then at least ×100
```
