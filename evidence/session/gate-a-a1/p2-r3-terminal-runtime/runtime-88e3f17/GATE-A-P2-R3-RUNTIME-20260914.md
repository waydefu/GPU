# Gate A P2 R3 FAIL — 88e3f17 terminal/observability — 2026-09-14

Exactly one fresh `p_r3_single_direct` after R0/R1/R2 PASS on `88e3f17`.
PROTO=1 TELEMETRY=1. Fresh COLD Activity displayId=0. Fresh X `:3`.
Stable PID **16085**. Teardown `NO_X3_RESIDUE` / collector NONE.
Do **not** silent-retry this cell. Do **not** proceed to R4.

## Runtime

| | |
|---|---|
| Activity / renderer | PID **18496** (GL drain tid **31080**) |
| X `:3` | PID **31868** died after fixture |
| Fixture | `FAIL GetImage` `FIXTURE_EXIT=1` |
| GATEA_EVENT | 1 (renderer REGISTER_READY only) |

```text
17:22:13.187 pid=18496 GATEA_BIND bound=1
17:24:02.849 pid=18496 GATEA_PEEK magic=1 bound=1
17:24:02.849 pid=18496 GATEA_HANDLE type=1 id=6
17:24:02.849 pid=18496 tid=31080 GATEA_DRAIN imports=1 overflow=0
17:24:02.849–.850 tid=31080 GATEA_VALIDATE … VALIDATE_TERMINAL_READY result=1
17:24:02.850 tid=31080 GATEA_EVENT seq=0 role=2 event=1 src=6
             (= RENDERER REGISTER_READY)
17:24:04.849 pid=31868 GATEA_FATAL_HALT what=x-ready-timeout reason=4
17:24:04.879 pid=18496 GATEA_FATAL_HALT what=r-hup reason=6
```

`type=1` is `LORIE_GATEA_MSG_REGISTER`. Timeout is exact 2.000s after
HANDLE. That is the X waiter, not a missing-log hang.

## VALIDATE stages (complete through READY send)

All `result=1` except `GL_ERROR result=0` (no GL error):

```text
VALIDATE_ENTER
TUPLE_MATCH
EGL_DISPLAY_PRESENT
EGL_CONTEXT_PRESENT
NATIVE_CLIENT_BUFFER_CAPABLE
CLIENT_BUFFER_ENTER / RETURN
CREATE_IMAGE_ENTER / RETURN
TEXTURE_CREATE_RETURN
IMAGE_TARGET_ENTER / RETURN
GL_ERROR (result=0)
READY_SEND_ENTER / RETURN
VALIDATE_TERMINAL_READY
```

Absent VALIDATE stages: `TUPLE_MISMATCH`, `EGL_NO_DISPLAY`,
`EGL_NO_CONTEXT`, `FAILED_SEND_*`, `VALIDATE_TERMINAL_FAILED`,
`VALIDATE_TERMINAL_FATAL`.

LAST VALIDATE STAGE: **VALIDATE_TERMINAL_READY**
NEXT MISSING STAGE: **X-side REGISTER_READY consume / waiter satisfaction**
(no `role=1` GATEA_EVENT; X jumps to `x-ready-timeout`)

## What this proves / does not prove

`8479997` silent-validate hypotheses are **falsified on this APK**:

- not tuple mismatch
- not EGL_NO_DISPLAY / EGL_NO_CONTEXT
- not missing native client-buffer
- not EGLImage / texture / GL failure
- not a silent return before READY send
- READY send returned success and renderer published
  `LORIE_GATEA_EVENT_REGISTER_READY`

Root cause of X timeout is **NARROWED, not proven**. Remaining locus is
after renderer `READY_SEND_RETURN`: X did not observe READY (demux /
waiter / cross-process socket delivery). No CPU/D0a/legacy fallback
occurred. Direct lease/publish/consume/fence never ran.

No SIGSEGV / SIGILL / SIGABRT. NEW CRASH: **NONE**.

Do **not** retry R3 on `88e3f17` / `8479997` / `6c7ee6f` / `98b0011`.
No source change. No timeout lengthening. Production stays BLOCKED.
R4–R10 NOT RUN.

Evidence: `r3-single-direct/`.
