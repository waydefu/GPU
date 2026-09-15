# R6-D1-retry4 — FAIL missing Present CALLBACK; pixels PASS; CLIENT_OK

Authorized 2026-09-15: official-docs fixture fix after retry3 BadGC, then one D1 cell.
Device stayed `9369553`. Prior cells not overwritten.

Official:

- `xcb_poll_for_reply`: 1 if reply/error received, 0 if not yet.
  https://xcb.freedesktop.org/ProtocolExtensionApi/
- `xcb_create_gc`: drawable must exist (`xcb_drawable_error_t`).
  https://www.x.org/releases/current/doc/man/man3/xcb_create_gc.3.xhtml
- `xcb_copy_area`: `xcb_gc_error_t` if GC does not exist (protocol BadGC=13).
  https://www.x.org/releases/current/doc/man/man3/xcb_copy_area.3.xhtml

Fixture change vs retry3 ELF: CreateGC on connection B only after `sync_conn(a)`.

| | |
|---|---|
| X `:3` | PID **7648** ALIVE then torn down |
| Fixture | source `3ca2f77c…bf91` ELF `8a3b8509…a953` |
| Script exit | **2** `R6_DESIGN_FAIL d1_missing_callback_after_request_present` |
| Fixture stdout | `CLIENT_OK` `PASS D1-composite-dst exact_px=64 got0=00804000` |
| Env | PROTO=1 TELEMETRY=1; OOM unset |
| Fatal | none |
| Stable | PID **1004** UNTOUCHED; `NO_X3_RESIDUE` |

REQUEST vs SUCCESS:

```text
seq 19 Render Composite (138.8)
seq 20 CALLBACK xop=3
seq 35 SEMANTIC_SUCCESS serial=6
seq 44 CopyArea REQUEST then CALLBACK xop=1
seq 48 PolyFillRectangle REQUEST then CALLBACK xop=2
seq 53 GetImage REQUEST then CALLBACK xop=5
seq 55 PresentPixmap REQUEST (146.1)
         no CALLBACK xop=4
```

Wait-pump of Copy/Solid/GetImage/Present REQUEST **FALSIFIED**. Pixels **PASS**.
CopyArea BadGC **FALSIFIED** on this ELF.

**PROVEN:** Present CALLBACK (`xop=4`) is emitted only when
`lorieTryScheduleGpuCopy` succeeds in `present_execute_copy` (source
`present_execute.c` ~111–120). Software `present_copy_region` else-branch
emits REQUEST but no CALLBACK. Design §9 still requires CALLBACK for each
fixture op.

Do not patch server C without a new grant. Do not silent-retry this cell.
