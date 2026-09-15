# GATE P2-B.2 — Over ARGB→XRGB no-mask GPU slice

```
P2-B.2: PASS (R3)
P2-B.2c corrected pixel oracle: PASS  tests=1514 fail=0 exact_px=1396616 ±1_px=0 Xnz=0 maxΔ=0
P2-B.2d stress: PASS
  x100 ok=100 fail=0; mixed100 ok=100 fail=0; x1000 ok=1000 fail=0
P2-B.2e bounded isolated XFCE: PASS
  45s; D0/D1/D2/D3=1637/1637/1637/1638; ENTER/RETURN=1638/1638;
  Fatal/SIGSEGV/SIGILL=0
Device APK: com.waydefu.x11gpu 1.03.01-9822435-07.09.26
  SHA256 cb5dbb8909c09d83bf92512792966bc7060153421829a99d52cafbc115ca197c
X :3 PID 29225 ppid=1  Stable :1 PID 26474 untouched
Gcomp full-oracle window FDCLONE=1515  Prepare TRUE=1515  RECT=1515  Done=1515  FALSE=0
```

P2-B.1 remains **CLOSED / PASS**. P2-A remains **CLOSED**. GPU Over is exact RGB on the corrected valid source path.

Slice not widened. Mask / two-pass / transform / bilinear not implemented. sys_ptr / PixmapIsOffscreen / Damage / depth-bailout unchanged. A.3/A.4 stamps left on. No PR.

Current next gate: **P2-B.3 real-workload performance qualification**. This has not yet been run; no desktop speedup claim is made here.

---

## R3 provenance and corrected oracle

- Valid per-pixmap-GC smoke wrote source REGULAR bytes correctly:
  `ffff0000`, `80800000`, and `80800000` for opaque red, alpha=80 red,
  and 5x24.
- S0 REGULAR was correct; S1 newly allocated AHB was zero before copy; S2
  AHB after copy matched S0; S3 FD staging matched S2.
- Smoke output was exact: `00ff0000`, `00800000`, `00807f00`.
- Corrected oracle: `tests=1514 fail=0 exact_px_acc=1396616 ±1_px=0 Xnz=0
  maxΔ=0`; negative controls `src-op`, `mask-a8`, `dst-argb`, `bilinear`,
  and `repeat` all completed in software.
- The superseded 1094-fail result used a root depth-24 GC for depth-32
  source PutImage and returned `BadMatch` error 8, leaving the source
  request zero. It was a client harness error, not a production boundary.
- Evidence: `evidence/session/p2-b2/retry-r3-provenance/`.

## Safety (live 2026-09-08T07:30:00+08:00)

- Stable `:1` PID **26474** ppid=4718 `termux-x11 com.termux.x11 :1 -legacy-drawing` — alive through all three APK installs and oracles. DISPLAY `:1` was not queried.
- Experimental only: `com.waydefu.x11gpu` `1.03.01-9822435-07.09.26` on `:3` PID **29225** ppid=1.
- Stable package still `com.termux.x11` `1.03.01-11b82d9-06.09.26` lastUpdateTime 2026-09-07 22:55:03.
- Bounded isolated XFCE on `:3` ran 45s then was stopped. Existing XFCE on stable `:1` was not touched.
- No PR.

---

## APK ladder (waydefu only; historical, superseded by R3)

The three oracles below used the invalid root depth-24 GC harness: tests=1514 **fail=1094** exact_px=389108 ±1_px=320972 Xnz=0 maxΔ=255. got==dst. Passes are a=0 / identity where expected==dest. Device is no longer on these APKs.

### 1. `42d2e3b` — first GPU Over slice

| | |
|---|---|
| commit | `42d2e3ba7da3aedf6791db5549f109be0a71e08f` `f8-p2-b2-over` |
| CI | **34163118589** success |
| APK | `1.03.01-42d2e3b-07.09.26` SHA256 `e47c55164397f356cb4806939e0c9508de3b06fdaa0afde2f793fa6a772a3985` |
| `:3` | PID **29619** ppid=1 |
| renderer | srcTex/dstTex nonzero, **swizzle=1** op=2 |
| diagnosis | BGRA AHB EGLImages sample black on this GPU; blend with As=0,Cs=0 leaves dest. RGBX Copy/Solid dest still works. |
| evidence | `evidence/session/p2-b2/` (`oracle.out.txt`, `pixel-dump.txt`, logcat `--pid=29619`) |

Install: `adb push` `/data/local/tmp/p2b2-waydefu.apk`; `pm install -r -t --user 0` hung; session `1657764756` create/write/commit → Success.

### 2. `15a4be3` — skip BGRA EGLImage, upload as GLES RGBA

| | |
|---|---|
| commit | `15a4be3c731d7c5b4e33703a7a8a614c8fbf0837` |
| CI | **34165324258** success |
| APK | `1.03.01-15a4be3-07.09.26` SHA256 `4397524ccc2d12ef7748181ea910307373eadcb300076521f00f8fda8f256d39` |
| `:3` | PID **27379** ppid=1 |
| renderer | **swizzle=0** (new code loaded) |
| diagnosis | Unlocking live AHB so renderer can `AHardwareBuffer_lock` did not change GetImage. Dest still unmodified. |
| evidence | `evidence/session/p2-b2/retry-15a4be3/` |

### 3. `d7de868` — FD snapshot of locked BGRA src (superseded; was live PID 13655)

| | |
|---|---|
| commit | `d7de86875e26c4c3c2a7f68e64de67efe5989584` |
| CI | **34166400010** success |
| APK | `1.03.01-d7de868-07.09.26` SHA256 `55a4b04bebf4e1fcffbaff677a981ab40e5cc8e192986583aedc4372c4cf6c57` |
| install | stop `:3` + `am force-stop com.waydefu.x11gpu`; session `2031415494` create/write/commit → Success |
| `:3` | PID **13655** ppid=1 (historical) |
| Gcomp | FDCLONE **1515** Prepare TRUE **1515** RECT **1515** Done **1515** FALSE **0** |
| clone px0 | **00000000 on 1515/1515** |
| evidence | `evidence/session/p2-b2/retry-d7de868/` (`oracle.out.txt`, snap FDCLONE stamps) |

The FD clone ran. It copied **zeros** from `priv->locked` at PrepareComposite. R3 later showed those zeros were the invalid tester's failed depth-32 PutImage (`BadMatch` 8), not an AHB converter discard: valid PutImage S0 was nonzero and S2/S3 preserved it.

---

## B.2c pixel oracle (historical invalid harness; same numbers on the three APKs above)

Invalid tester: one root depth-24 GC for depth-32 source PutImage. `DISPLAY=:3 /tmp/p-b2-oracle`. Superseded by R3 corrected oracle (`fail=0`).

| | |
|---|---|
| tests | **1514** |
| fail | **1094** |
| pass | 420 (a=0 Over + identity where expected==dest) |
| exact_px_acc | 389108 |
| ±1_px | 320972 (a=01 dest-unchanged vs dest±1 expected — **not UNORM PASS**) |
| Xnz | **0** |
| maxΔ | **255** |
| got==dst | FAIL tests |
| tester rc | 1 |

### Samples (got vs expected)

| case | src | dst | got | expected | maxΔ |
|---|---|---|---|---|---:|
| 1×1 a=ff white on black | `ffffffff` | `00000000` | `00000000` | `ffffffff` | 255 |
| 1×1 a=ff red on black | `ffff0000` | `00000000` | `00000000` | `ffff0000` | 255 |
| 1×1 a=7f black on white | `7f000000` | `00ffffff` | `00ffffff` | ~`007f7f7f` | 127 |
| 1×1 a=01 | `01000000` | `00ffffff` | `00ffffff` | dest−1 | 1 |

FAIL by alpha: `a=01` 348; `a=7f/80/fe/ff` 186 each; `a=00` 0 (correct no-op).

`Prepare TRUE ≈ gpu_rects ≈ Done`. Path is GPU. Pixels are wrong.

---

## Negative controls (`42d2e3b`; later APKs kept the same fail-closed predicate)

Oracle built-in (after positives). Extra on first APK: transform, componentAlpha.

| kind | Composite | X alive | Prepare TRUE increment |
|---|---|---|---|
| src-op | completed | yes | no |
| mask-a8 | completed | yes | no |
| dst-argb | completed | yes | no |
| bilinear | completed | yes | no |
| repeat | completed | yes | no |
| transform | completed | yes | **0** |
| componentAlpha | completed | yes | **0** |

---

## B.2d / B.2e

R3 stress and bounded XFCE both passed; see the R3 evidence directory.

B.1 XFCE baseline (historical, not re-measured): GPU Composite **0**, Over-none still in fb **1166 / 1776**. R3 now proves pixel correctness; the GPU-vs-pixman comparison is deferred to P2-B.3.

---

## Next gate

P2-B.2c/d/e are complete. The current next gate is **P2-B.3
real-workload performance qualification**. Keep the Over predicate narrow and do not widen mask,
two-pass, transform, bilinear, repeat, or componentAlpha support.

---

## Live at write-up (2026-09-08T07:30:00+08:00)

| | |
|---|---|
| `:1` | PID **26474** ppid=4718 `termux-x11 com.termux.x11 :1 -legacy-drawing` |
| `:3` | PID **29225** ppid=1 `termux-x11gpu com.waydefu.x11gpu :3` |
| APK | `com.waydefu.x11gpu` `1.03.01-9822435-07.09.26` |
| commit on device | `98224356e40913dcf2188d18748eba9401639850` |
| XFCE on `:3` | **not started** |

---

## Verdict

**PASS (R3).** Valid per-pixmap-GC source writes reach REGULAR backing,
S0→S1→S2→S3 preserve exact source bytes, GPU Over output is exact RGB, and
all negative controls remain software. Stable `:1` PID 26474 remained
untouched. Stress and bounded XFCE both passed.
