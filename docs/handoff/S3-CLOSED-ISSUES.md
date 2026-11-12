# S3 Closed Issues (sealed; reopen only on fresh contradictory evidence)

## Historical +768 (non-legacy root geometry)

- Symptom: +768 px geometry shift seen in early non-legacy trials (2/2 once).
- Root cause: lifecycle artifact of the experimental session bring-up, not a renderer offset.
- Fix: N/A (stopped reproducing).
- Validation: debug5 `c698164` Case A/B/C 3/3 did not reproduce; P0 Gates 1–4 PASS.
- Current status: historical regression note inside CLOSED P0.
- Do-not-reopen boundary: never re-attribute to renderer offset without a fresh reproduction.

## P2-A Composite recursion crash

- Symptom: `Fatal signal 11 SEGV_ACCERR` after `Sent shared buffer width 1 stride 64 height 1`; flight last request `op=138.8 RENDER Composite PictOpOver`, phase ENTER; minimal repro `patches/p_render_last.c` 1×1.
- Root cause: double-installed histogram/XRender probe — `damageComposite ↔ lorieCompositeProbe` recursion (NOT pitch/backing/fb/pixman, NOT `sys_ptr`, NOT `PixmapIsOffscreen`, NOT Damage lifecycle).
- Fix: `6182b94` make probe install-once (+ A.3/A.4 observe-only stamps, left on).
- Validation: post-fix probe depth max 1; bounded isolated XFCE 45 s, zero fatal/SIGSEGV/SIGILL.
- Current status: P2-A CLOSED.
- Do-not-reopen boundary: backing/pitch theories stay closed.

## Tester 1094 (superseded P2-B.2 oracle failure)

- Symptom: 1514 tests / 1094 fail, maxΔ=255, got==dst.
- Root cause: tester bug — one root depth-24 GC used for depth-32 source PutImage → `BadMatch` (error 8), source stayed zero. NOT a GPU slice defect.
- Fix: corrected per-pixmap-GC tester; production slice unchanged.
- Validation: corrected oracle 1514/1514, 1396616 exact px, ±1=0, maxΔ=0, Xnz=0; negative controls (src-op/mask-a8/dst-argb/bilinear/repeat) stay software.
- Current status: superseded; R3 PASS stands on the corrected oracle.
- Do-not-reopen boundary: never cite the 1094 fail as an R3 correctness defect; ±1 UNORM never counts as PASS.
