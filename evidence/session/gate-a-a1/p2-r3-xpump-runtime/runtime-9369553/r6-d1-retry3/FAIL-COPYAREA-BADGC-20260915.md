# R6-D1-retry3 — FAIL CopyArea BadGC; pixels PASS; schedule constructed

Authorized 2026-09-15: one bounded D1 rerun of retry2 ELF after ART JIT 28170.
Device stayed `9369553`. Prior cells not overwritten.

| | |
|---|---|
| X `:3` | PID **2555** ALIVE then torn down |
| Fixture ELF | `63433803…70a8` (retry2: PolyFill onto `copypm`) |
| Script exit | **2** `R6_DESIGN_FAIL fixture_rc` |
| Pixels | **PASS** `exact_px=64 maxΔ=0 got0=00804000` |
| Fixture | `FAIL D1 CopyArea err=13` |
| Env | PROTO=1 TELEMETRY=1; OOM unset |
| Stable | PID **1004** UNTOUCHED; `NO_X3_RESIDUE` |
| JIT 28170 | **NON-REPRODUCED** on this cell |

REQUEST order:

```text
seq 19 Render Composite (138.8)
seq 35 SEMANTIC_SUCCESS serial=6
seq 44 CopyArea (62)
seq 45 PolyFillRectangle (70)
seq 46 GetImage (73)
seq 48 PresentPixmap (146.1)
```

Wait-pump of second ops remains **FALSIFIED**. Pixel dest-Solid race **FALSIFIED** on this ELF.

**PROVEN:** protocol error 13 is X **BadGC** (`xcb_copy_area` `xcb_gc_error_t`: specified GC does not exist). retry1 never reached this check because pixels failed first.

**INFERRED then bound by official man:** B `CreateGC` used A's `copypm` before A's CreatePixmap was processed → CreateGC `BadDrawable` (unchecked) → GC never defined.

Official:
- https://www.x.org/releases/current/doc/man/man3/xcb_copy_area.3.xhtml
- https://www.x.org/releases/current/doc/man/man3/xcb_create_gc.3.xhtml
- https://xcb.freedesktop.org/ProtocolExtensionApi/ (`xcb_poll_for_reply` 0/1; no change to wait loop)
