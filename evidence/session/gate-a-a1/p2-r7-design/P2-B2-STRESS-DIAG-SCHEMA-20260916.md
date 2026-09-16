# p_b2_stress diagnostic schema — 2026-09-16

Host/client fixture only. Does **not** change `a7528bd`, libXlorie, APK, or
frozen R6. Does **not** overwrite `runtime-a7528bd/r1-unset-oracle/`.

## Old harness (opaque)

`patches/p_b2_stress.c` printed only:

```text
STRESS mixed=%d ok=%d fail=%d n=%d alive=%d
```

`fail` collapsed: ALLOC / PutImage-src / PutImage-dst / Composite X error /
GetImage no-reply (error discarded) / RGB mismatch / X-byte ≠ 0.

Could not name iteration, stage, expected/got, or monotonic time.

## Success path (unchanged)

No per-iteration print, no sleep, no retry, no extra GetImage, no extra
checked round-trip. Request order of a successful `one()` remains:

generate ids → calloc → CreatePixmap×2 → CreateGC×2 → PutImage-checked src →
PutImage-checked dst → CreatePicture×2 → SetFilter → Composite-checked Over →
GetImage 1×1 (0,0) of dest → FreePicture×2 → FreeGC×2 → FreePixmap×2.

Pass criterion unchanged:

```text
(got & 0xffffff) == expected && ((got >> 24) & 255) == 0
```

Final summary line unchanged in meaning:

```text
STRESS mixed=%d ok=%d fail=%d n=%d alive=%d
```

Qualification remains `fail == 0`.

## Failure path (new, once per failed iteration)

Exactly one line, prefix `B2_DIAG_FAIL`, fields always present. Inapplicable
values are the sentinel `NA` (never omitted).

```text
B2_DIAG_FAIL iteration=%d start_mono_ns=%llu fail_mono_ns=%llu stage=%s w=%u h=%u alpha=%u mixed=%d sc=0x%06x dc=0x%06x src_px=%s dst_px=%s put_src_err=%s put_dst_err=%s composite_err=%s getimage_reply=%s getimage_err=%s expected=%s got=%s rgb_expected=%s rgb_got=%s x_expected=%s x_got=%s conn_err=%d sequence=%s
```

| Field | Meaning |
|---|---|
| iteration | `one()` index `i` (0-based) |
| start_mono_ns | `CLOCK_MONOTONIC` at iteration start (memory-only until fail) |
| fail_mono_ns | `CLOCK_MONOTONIC` when failure classified |
| stage | see below |
| w, h, alpha, mixed, sc, dc | recipe to recompute expected pixel |
| src_px, dst_px | premul src / dest fill; `NA` if before they exist |
| put_src_err / put_dst_err / composite_err | X `error_code` or `NA` |
| getimage_reply | `1` / `0` / `NA` |
| getimage_err | X `error_code` or `NA` |
| expected / got | `0x........` or `NA` |
| rgb_expected / rgb_got | low 24 bits or `NA` |
| x_expected | always `0x00` once expected exists, else `NA` |
| x_got | high 8 bits of got, or `NA` |
| conn_err | `xcb_connection_has_error()` at classify time |
| sequence | failing request cookie/`full_sequence` if known, else `NA` |

Stages:

- `ALLOC_FAIL`
- `PUT_SRC_XERROR`
- `PUT_DST_XERROR`
- `COMPOSITE_XERROR`
- `GETIMAGE_NO_REPLY` (reply NULL and error pointer NULL)
- `GETIMAGE_XERROR` (reply NULL and error pointer non-NULL)
- `PIXEL_RGB_MISMATCH`
- `PIXEL_XBYTE_MISMATCH`

If RGB and X-byte both mismatch: stage is `PIXEL_RGB_MISMATCH`; both rgb and
x fields are still printed.

## Timing / request limitations (deliberate)

CreatePixmap / CreateGC / CreatePicture / SetFilter stay **unchecked** (same as
before). A failure there is **not** a new stage; it still surfaces as a later
PUT/COMPOSITE/GETIMAGE error. Adding checks would insert round trips.

GetImage still uses the original unchecked `xcb_get_image` + `reply`. The only
change is passing an error out-parameter instead of `NULL` so GETIMAGE_XERROR
can be distinguished. Same request, no extra round trip.

PutImage and Composite were already `_checked` + `xcb_request_check`. Diagnostics
only keep `error_code` / sequence before `free(e)`.

No `xcb_aux_sync`, no `GetInputFocus`, no retry, no sleep.

## Correlation

Compare `start_mono_ns`/`fail_mono_ns` against logcat `EXA GPU composite wait
timeout` and SurfaceFlinger dequeue delays on a **future** authorized cell
directory, e.g. `runtime-a7528bd/r1-unset-diagnostic-01/`. Client monotonic
ns is not wall-clock; bind via the process lifetime and nearby `Gcomp Done`.

## Future run

Do not overwrite `runtime-a7528bd/r1-unset-oracle/`.
Device reproduction requires separate authorization.

## RED → GREEN (host, 2026-09-16)

1. `cc ... test-p_b2_stress_diag.c` without `p_b2_stress_diag.h` → fatal
   `p_b2_stress_diag.h: No such file or directory` (**RED**).
2. Helper implemented; `cc -Wall -Wextra -Werror` + `./test-p_b2_stress_diag`
   → `test-p_b2_stress_diag PASS` (**GREEN**).
3. Fixture `cc -Wall -Wextra -Werror -O2 -lxcb -lxcb-render` rc=0.
