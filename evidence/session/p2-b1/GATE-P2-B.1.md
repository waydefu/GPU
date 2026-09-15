# GATE P2-B.1 — XRender/EXA Composite acceleration baseline

> **歷史 gate snapshot。** 本檔記錄 B.1 census 當時 `PrepareComposite=FalseNoop`、GPU Composite=0 的基線；後續 P2-B.2 R3 已完成窄 Over GPU slice。不要用本檔的舊「未實作」文字覆蓋目前 verdict，現況以 `HANDOFF.md` 與 `evidence/session/p2-b2/GATE-P2-B.2.md` 為準。

```
P2-B.1: CLOSED / PASS
Census only — rendering semantics unchanged.
Dispatch chain recovered (not probe-only):
  damageComposite → lorieCompositeProbe → exaComposite
    → EXA Copy/solid  OR  ExaCheckComposite → fbComposite → pixman
    → (Over+mask subset) two-pass OutReverse+Add then fb
max_depth = 1
enter = return = 1776  (XFCE window)
D3 = 1776
every probe call-through hit E0
GPU PrepareComposite = 0  (FalseNoop)
1×1 PASS (A.4d)
5×24 Over PASS (64× in XFCE, all fbComposite, all returned)
SIGILL/SIGSEGV = 0
Stable :1 PID 26474 untouched
```

P2-A remains **CLOSED**. This gate only measures where Composite goes after the hook-cycle fix, and names the first GPU slice from **observed** frequency — not from a guessed Over.

No `PrepareComposite` implementation. No sys_ptr / pitch / Damage / depth-bailout change. No commit.

---

## Safety

- Stable `:1` PID **26474** `termux-x11 com.termux.x11 :1 -legacy-drawing` ppid=4718 — live at B.1 write-up.
- Experimental `:3` PID **32075** ppid=1 `termux-x11gpu com.waydefu.x11gpu :3` — same A.4a–A.4e instance, still up. Isolated `:3` xfwm4 PID **11216** still running; `:1` xfwm4 **27716** not touched.
- APK `com.waydefu.x11gpu` `1.03.01-6182b94-07.09.26` SHA256 `9f2f8651378c3bbd3cbccff0566538d64af7cf22e349c874c470d848935cd42b`

---

## Method

Reuse A.4e XFCE logcat (`a4e-logcat-live.txt`), not a new desktop session.

Pair each `Probe ENTER` with `enter >= 106` (first XFCE Composite after A.4d’s 105) through `D3 AFTER_CALL`:

- 1776 / 1776 probes have a following `E0 EXA_COMPOSITE_ENTER`
- 1776 / 1776 have `Probe RETURN` and `D3`
- `saved` is always `exaComposite` `0x7498d416e0` (not `damageComposite`, not self)

That is the A.3 missing chain. A.3 had `E0=E0u=E1=Sfb=0` because recursion never left the probe. Here the lower Composite **runs and returns**.

1×1 is A.4d (`p-render-last 1x1`), not in the XFCE window. Gate 2 `5×24 Over` appears 64 times in XFCE; all took `fbComposite` and returned.

Formats for the dominant cell come from the 5s histogram (`src=20028888` = `a8r8g8b8`, `dst=20020888` = `x8r8g8b8`, `mask=0`, `flags=0x0`, `filter=0`). Histogram dump is top-8 per 5s (tail undercount); **shape counts below are complete** from the 1776 paired first-E0 records.

Machine-readable: `census.json`.

---

## Dispatch chain (recovered)

```
D0  damageComposite
      → lorieCompositeProbe          enter=return, max_depth=1
        → E0 exaComposite            1776 / 1776 probes
           ├─ exaHWCopyNtoN / solid  315  no E0u  (existing EXA Copy/Solid GPU)
           ├─ two-pass helper        127  nested OutReverse+Add, then fb
           └─ E0u ExaCheckComposite  1334
                → E1 fbComposite
                → Sfb pixman bits
        → Probe RETURN
D3  damageComposite return
```

At the time of this B.1 census, `PrepareComposite` was still `FalseNoop` and the driver accepted no Composite on the GPU. Copy-shaped `PictOpSrc` (and some opaque Over) never call it; EXA special-cases them to `exaHWCopyNtoN`. P2-B.2 later added only the narrow Over slice described in the current handoff.

---

## Fallback classes (every XFCE Composite)

| Class | PrepareComposite | Actual lower path | Ops | % ops | Pixels | % px |
|---|---|---|---:|---:|---:|---:|
| **fbComposite / pixman** | FALSE (`FalseNoop`) or never reached after Copy miss | `ExaCheckComposite` → `fbComposite` → pixman | **1334** | 75.1% | 27.8M | 11.4% |
| **EXA Copy/solid shortcut** | not consulted | `exaHWCopyNtoN` / solid / tiled / empty-region `done` — **no E0u** | **315** | 17.7% | 205.5M | 84.1% |
| **two-pass then fb** | FALSE, then `exaTryMagicTwoPassCompositeHelper` | nested `OutReverse` + `Add` (127 extra E0 pairs), then fb | **127** | 7.2% | 10.9M | 4.5% |
| **GPU Composite** | would be TRUE | `PrepareComposite` + Composite/Done | **0** | 0% | 0 | 0% |

Reason codes:

- `prepare_composite_noop` — `PrepareComposite = FalseNoop` (function pointer non-NULL, always FALSE).
- `copy_shortcut` — `!mask && (Src || Over without src alpha) && formats compatible` → existing GPU Copy. Dominated by **65× 1200×2191 Src** (170.9M px).
- `two_pass_ca_or_solid_mask` — Over + mask, component-alpha or solid src; in the B.1 snapshot EXA split then still fell to fb because the Composite GPU path was not yet implemented.
- `unaccel_fb` — remaining Over (especially ARGB src) and leftover Src.

A.4e `E0=2030` vs `D0=1776` is the 254 nested two-pass E0s (`127×2`), not double-counting at the probe.

---

## XFCE workload (first E0 after probe)

Op mix: **Over 1479 (83.3%)**, Src 295 (16.6%), Saturate 2.

| Shape (op, mask, size) | Path | Ops | % ops | Pixels |
|---|---|---:|---:|---:|
| Over, none, 17–64 | fbComposite | **981** | **55.2%** | 0.49M |
| Src, none, 2–16 | fb or Copy | 175 | 9.9% | ~13k |
| Over, mask, 257–1024 | Copy / two-pass / fb split | 138 | 7.8% | 29.2M |
| Over, none, 257–1024 | fb or Copy | 100 | 5.6% | 26.2M |
| Over, none, 2–16 | fbComposite | 80 | 4.5% | 18k |
| Src, none, >1024 (1200×2191) | **EXA Copy** | 65 | 3.9% | **170.9M (74% px)** |
| Over, none, >1024 | mostly fb | 60 | 3.4% | 1.9M |
| 5×24 Over none | fbComposite | **64** | 3.6% | — |

Over + mask none + **still in fbComposite**: **1166 / 1776 (65.7%)**. Histogram cell for the 17–64 bucket: `op=3 src=a8r8g8b8 mask=none dst=x8r8g8b8 flags=0x0 filter=0`.

---

## First GPU candidate (from census, not guess)

```
First GPU candidate:
op          = PictOpOver
src         = a8r8g8b8
mask        = none
dst         = x8r8g8b8
constraints = no transform, filter nearest, no componentAlpha,
              no repeat, ordinary pixmap
observed frequency = 1166/1776 XFCE Composite (65.7%) still software;
                     981/1776 (55.2%) are 17–64px Over none fb
                     (hist: a8r8g8b8 → x8r8g8b8, flags=0x0)
```

Why this slice, not fullscreen Src: those 65 Src 1200×2191 ops are **already** `exaHWCopyNtoN` (existing GPU Copy). Accelerating them again as Composite would duplicate a qualified path and ignore the compositor’s actual software pile — ARGB `Over` without mask, which **cannot** use the Copy shortcut (`PICT_FORMAT_A(src)` is set).

Why not Over+A8 mask yet: 250 Over+mask ops split across Copy-shaped, two-pass, and fb; two-pass is 7.2% and needs component-alpha / solid-src handling. Second slice for B.2+ after the none-mask Over path is correct.

B.2 must not change this census’s semantics except by implementing `PrepareComposite` for **exactly** this slice and keeping every other case on the paths above.

---

## PASS checklist

- [x] `damageComposite ↔ probe` acyclic, `max_depth=1`
- [x] Real EXA/fb software path reached **and returned** (1334 fb; 64× 5×24 Over; A.4d 1×1)
- [x] Interpretable XFCE histogram + complete first-E0 census (1776)
- [x] Every class has a fallback reason
- [x] No SIGILL / SIGSEGV
- [x] `:1` PID 26474 untouched
- [x] First GPU candidate written from observed frequency

**At the time:** Next was P2-B.2 — first narrow GPU Composite slice (Over, a8r8g8b8→x8r8g8b8, mask none, no transform/CA/repeat). Pixel correctness was completed in **P2-B.2c**; the current next gate is **P2-B.3 real-workload performance qualification**.
