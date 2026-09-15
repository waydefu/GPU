# GATE P2-A.4d — Composite regression matrix + ×100

> 歷史 gate 證據。本文的 PID、APK 與觀測窗口只描述 A.4d；P2-A 已關閉，目前 runtime 以 `HANDOFF.md` 為準。

```
P2-A.4d: PASS
1×1 DEST          PASS  (PictOpDst no-op; X alive; no D0 — expected)
1×1 SRC           PASS  D0=1 D3=1 ENTER=1 RETURN=1 max_depth=1
16×16 MASK        PASS  D0=1 D3=1 ENTER=1 RETURN=1 E0u/E1/Sfb src+mask+dst
p-render-last 1x1 PASS  D0=1 D3=1 ENTER=1 RETURN=1 max_depth=1
p-render-last 5x24 PASS (default / xfwm-shaped) D0=1 D3=1 E0u/E1/Sfb
Original Composite = p-render-last 1x1 (same as crash repro); 5x24 is seq-404 shape
×100 1x1          PASS  D0=100 D3=100 ENTER=100 RETURN=100 max_depth=1
Ssig/Uctx/Fatal   0
X :3 PID 32075 ppid=1  xdpyinfo ok
Stable :1 PID 26474 untouched
P0/P1 not reopened
Next gate at the time: XFCE / original P2 workload qualification (:3 only; completed by A.4e). Current next gate: P2-B.3 performance qualification.
```

A.4a remains **PASS**. A.4b remains **PASS**. A.4c remains **PASS**. A.3 remains **ROOT CAUSE CONFIRMED** (sealed). This gate only re-runs Composite survival on the install-once probe build. Did **not** start XFCE / xfwm on `:3`. Did **not** patch sys_ptr / pitch / PrepareAccess / Damage / histogram. No commit.

---

## Safety

- Stable `:1` PID **26474** `termux-x11 com.termux.x11 :1 -legacy-drawing` — alive PRE, after every case, after ×100, and at write-up (`2026-09-08T04:37:10+08:00`, elapsed ~05:41:00). DISPLAY `:1` was not queried.
- Experimental only: `com.waydefu.x11gpu` `1.03.01-6182b94-07.09.26` SHA256 `9f2f8651378c3bbd3cbccff0566538d64af7cf22e349c874c470d848935cd42b` on `:3` PID **32075** ppid=1 (same instance as A.4a/A.4b/A.4c). Reused; `xdpyinfo :3` ok throughout.
- No xfwm / XFCE on `:3`. Existing XFCE on stable `:1` was not touched.
- No `sys_ptr` / pitch / Damage-bypass / `if (depth > N) return` / SIGILL special-case / force software. Histogram probe left on. No commit / push / CI.

---

## Method

Reused live `:3` PID 32075. Testers:

| Case | Binary | Source |
|---|---|---|
| 1×1 DEST | `DISPLAY=:3 /tmp/p-a4d-roles dest` | `/tmp/p-a4d-roles.c` (from `patches/p_render_last.c`; copied to `p-a4d-roles.c`) |
| 1×1 SRC | `/tmp/p-a4d-roles src` | same |
| 16×16 MASK | `/tmp/p-a4d-roles mask-16x16` | 16×16 Over + a1 mask (A.2 last Sprep shape) |
| p-render-last 1x1 | `/tmp/p-render-last 1x1` | `patches/p_render_last.c` |
| p-render-last 5x24 | `/tmp/p-render-last 5x24` | default mode; closest to flight seq 404 |
| ×100 | `/tmp/p-render-last 1x1` ×100 | original P2 crash repro |

Original Composite reproducer is **`p-render-last 1x1`** (`evidence/session/p2-a-crash/`, HANDOFF.md). Distinct extra: **`p-render-last 5x24`** (filter nearest, 5×24, same shape as xfwm last request). `win` mode not run (window dest is closer to desktop; this gate stops before XFCE).

Deleted `run_composite_matrix.py` was not restored; DEST/SRC use the same PictOpDst / PictOpSrc cells as `evidence/session/composite-matrix/` (`1x1-aa-dst` 3/3 PASS historically; `aa-src` died).

---

## Case table

| Case | tester | X :3 | D0 | D3 | ENTER/RETURN | max_depth | Ssig | Notes |
|---|---|---|---|---|---|---|---|---|
| **1×1 DEST** | rc=0 PASS | 32075 | 0 | 0 | 0/0 | — | 0 | PictOpDst returns in `CompositePicture` before `ps->Composite` (`picture.c`); same historical live cell |
| **1×1 SRC** | rc=0 PASS | 32075 | 1 | 1 | 1/1 | 1 | 0 | op=1 1×1; E0 then RETURN (no E0u this flight) |
| **16×16 MASK** | rc=0 PASS | 32075 | 1 | 1 | 1/1 | 1 | 0 | op=3, mask present; E0u + Sfb src+mask+dst 16×16 bpp=1 MASK index=2 |
| **p-render-last 1x1** | rc=0 PASS | 32075 | 1 | 1 | 1/1 | 1 | 0 | original crash repro; Over→Src |
| **p-render-last 5x24** | rc=0 PASS | 32075 | 1 | 1 | 1/1 | 1 | 0 | default; E0u + Sfb src+dst |
| **×100 1x1** | 100/100 PASS | 32075 | 100 | 100 | 100/100 | 1 | 0 | lifetime enter=105 return=105 (includes A.4a + matrix) |

All listed cases **complete**. `:3` stayed PID 32075. Probe recursion still 0 (`max_depth==1` on every ENTER).

---

## ×100

`p-render-last 1x1` ×100, `04:35:48`–`04:36:00`. Checkpoints at i=1,10,20,25,40,50,60,75,80,100: tester PASS, `xdpyinfo :3` ok, PID 32075.

Snap window `a4d-x100.snap-window.txt`:

```
D0 = 100  depth max = 1
D3 = 100
Probe ENTER = 100
Probe RETURN = 100
max=1 on every ENTER
final Probe RETURN enter=105 return=105
Ssig = 0
```

enter≈return. Not 2× per request (100 Composite → 100 probe pairs).

---

## Snap / logcat highlights

Process-lifetime probe counters (PID 32075, including A.4a’s one 1×1):

| | |
|---|---|
| D0 depth max | **1** (logcat D0_n=104 this capture = matrix 4 + ×100; DEST adds 0) |
| D3 | pairs with D0 on every probe flight |
| Probe ENTER / RETURN | matrix 4/4 then ×100 100/100; lifetime **105 / 105** |
| max_depth | **1** |
| Ssig / Uctx / Fatal | **0** |

Histogram 5s dump after the matrix (`a4d-hist-dump.txt`):

```
04:35:47.431  xrender_ops=4
  hist[0] count=2 op=1  1×1 Src + 1×1 Over→Src   (not 4)
  hist[1] count=1 op=3  16×16 MASK  flags=0x1
  hist[2] count=1 op=3  5×24 nearest
```

Four probe Composites, four ops recorded. Histogram growth is allowed; this window is **not** 2× per request. DEST absent because it never entered the probe. No FPS dump during ×100 (pixmap-only; logcat stopped at 04:36:00). Pairing for ×100 is the snap counts above.

16×16 MASK path (the A.2 last-Sprep shape) now **returns**:

```
D0 op=3 maskDraw≠0 xywh=16,16
Probe ENTER max=1
E0 → E0u
  Sprep DEST index=0  16×16 bpp=32
  Sprep SRC  index=1  16×16 bpp=32
  Sprep MASK index=2  16×16 bpp=1  devKind=64
E1 PRE_FB fbComposite
Sfb src + mask + dst
Probe RETURN enter=3 return=3
D3 depth=1
```

1×1 SRC / p-render-last 1x1 this session: E0 then RETURN without E0u (EXA Src/copy path). A.4c already showed the unaccel/fb path on a fresh 1×1. Survival here is the gate; do not reopen backing/pitch.

Screen reported by testers is now **1200×2191** (A.4a was 1280×1024). Same PID 32075; RandR/activity resize only. Recorded, not a new investigation.

InstallProbe `installed=0` still `saved=exaComposite` after CloseScreen/RandR — A.3 cycle does not return.

---

## Live at write-up

| | |
|---|---|
| `:1` | PID **26474** ppid=4718 `termux-x11 com.termux.x11 :1 -legacy-drawing` |
| `:3` | PID **32075** ppid=1 `termux-x11gpu com.waydefu.x11gpu :3` (~25 min up, same as A.4a) |
| APK | `com.waydefu.x11gpu` `1.03.01-6182b94-07.09.26` SHA256 `9f2f8651378c3bbd3cbccff0566538d64af7cf22e349c874c470d848935cd42b` |
| stable pkg | `com.termux.x11` `1.03.01-11b82d9-06.09.26` |
| commit | `6182b94bc69166e49a2f6ca0238ffdba9781fc68` |

A.4a `stamps.txt` / A.4b hist / A.4c path window **kept**.

---

## Verdict

**PASS.** Every listed case completed with `:3` still 32075. ×100 of `p-render-last 1x1` survived. No SIGILL/SIGSEGV. Probe recursion still 0. `:1` still 26474. P0/P1 not reopened.

Do **not** start XFCE in this gate.

---

## Next after A.4d PASS — XFCE / original P2 workload qualification

Name only; **not run in A.4d**. Still on experimental `:3` only. Do not mix with stable `:1`.
