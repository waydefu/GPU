# Gate A P2 R3 — FAIL x-ready-timeout (98b0011) 2026-09-14

```
R3 FAIL
artifact: 98b0011 / e547eadb…1760 / Build ID 52053312…66cf
what=x-ready-timeout reason=4 (LORIE_GATEA_FAIL_TIMEOUT)
fresh Activity PID 30362 still r-hup after X halt
GATEA_EVENT=0 (no REGISTER_READY)
Production Gate A BLOCKED
```

`98b0011` (`fix(gatea): bind Activity Gate A from shared tuple, not getenv`)
was installed only over `com.waydefu.x11gpu`. R1 requal PASS, R2 requal PASS.
R3 still fail-stops on the 2 s READY wait. Stable `:1` PID **16085** unchanged.
HDMI observe-only. `NO_X3_RESIDUE`.

## Cells

| cell | Activity PID | X PID | result |
|---|---|---|---|
| `r3-single-direct` | **25253** (reused across earlier T2/R1/R2) | 32508 | FAIL GetImage; `x-ready-timeout`; then `r-hup` |
| `r3-single-direct-fresh` | **30362** (force-stop waited until gone, COLD start) | 7710 | same FAIL |

Stale Activity PID is **not** the remaining cause. Fresh process reproduces.

## Observation (fresh cell)

```
07:20:19.264  30362  XCB connection is successfull
07:20:20.006  30362  Received shared buffer … id 0   (EVENT_SHARED_SERVER_STATE ran)
07:20:28.116   7710  GATEA_FATAL_HALT what=x-ready-timeout reason=4
07:20:28.143  30362  GATEA_FATAL_HALT what=r-hup reason=6
```

No `GATEA_EVENT`. No `r-bad-frame` / `r-bad-register` / `x-register-send` /
`r-ready-send`. Client `FAIL GetImage` because X died.

## What 98b0011 did prove

`r-hup` is now gated on `lorieGateABoundTuple()`, not Activity getenv.
A fresh Activity that never had `TERMUX_X11_GATEA_PROTO` still fatals `r-hup`.
The Activity **did bind** a nonzero tuple. The original getenv-skip of
bind/peek/drain is therefore **not** the remaining timeout cause.

Share + `EVENT_ADD_BUFFER` completed ~8 s before EnsureReady. Bind had time.

## Remaining cause (not yet proven)

X sent REGISTER (else `x-register-send`) and waited 2 s. Renderer never
emitted `REGISTER_READY`. That means one of:

1. Activity peek did not treat the bytes as Gate A (`MSG_PEEK` miss) so
   `read()` consumed the frame as a `lorieEvent` (no `r-bad-frame`);
2. peek ran but `gateAHandleFrame` / enqueue / GL drain did not finish;
3. READY was sent and X did not demux it (would still usually leave a
   renderer `GATEA_EVENT REGISTER_READY`; none seen).

No current log distinguishes these. Next repair is a **diagnostic-only**
Activity bind/peek/handle log (version, nonce, generation, bound, peek),
then CI artifact and R1+R2 requalify before another R3. Do not keep
retrying R3 on `98b0011`.

## Evidence

- `r3-single-direct/` and `r3-single-direct-fresh/`
- `r3-fixture.out` — `FAIL GetImage`
- `logcat-follow.txt` / `logcat-dump-unfiltered.txt` — both fatals
- R1: `t2-*-*`, `r1-unset-oracle`, `r1-proto0-oracle`
- R2: `r2-imported-reject/`

Production Gate A stays **BLOCKED**. Do not enable Production. Do not
install superseded `dd81ac0` / `15caa00`.
