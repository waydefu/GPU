# Gate A P2 R1 on d9b7f60 — 2026-09-15 PROTO=0 rerun PASS; R3 later PASS

Artifact `d9b7f60` / `1.03.01-d9b7f60-14.09.26` / SHA256
`255cc37d12dd052c32d2b8ba89af3029034f59f7e01b65bd61cffd50d86737a2` /
Build ID `2b02bf139236d45aaa24a95fa8609cca0d956e7d` MATCH on-device.
CI run 34872266646. Production Gate A remains **BLOCKED**.
Stable `:1` PID **16085** untouched. HDMI observe-only. `--display 0` only.
R3 is recorded separately: `GATE-A-P2-R3-RUNTIME-20260915.md` (**PASS**).

```
R0 DEVICE PASS
R0 ARTIFACT INSTALL BINDING PASS
R1 UNSET oracle/stress PASS
R1 PROTO=0 STARTUP SIGSEGV OBSERVED (X PID 21639, signo=11, si_addr=0)
R1 PROTO=0 RERUN oracle/stress PASS (X PID 27435; 21639 NON-REPRODUCED)
R3 PASS (separate report)
21639 FORENSICS: dalvik-jit class, same family as 21977, root cause NOT PROVEN
```

## R1 unset — PASS

X PID **19391**. COLD Activity displayId=0.

| cell | oracle | x100 | mixed100 | x1000 | GATEA_EVENT | X |
|---|---|---|---|---|---|---|
| unset | 1514 fail=0 maxΔ=0 Xnz=0 | 100/100 | 100/100 | 1000/1000 | 0 | 19391 ALIVE then torn down |

`NO_X3_RESIDUE`. Stable 16085. No GATEA_FATAL_HALT.

Evidence: `r1-unset-oracle/`.

## R1 PROTO=0 first cell — FAIL (startup SIGSEGV, OBSERVED)

First logcat helper race (`r1-proto0-oracle-attempt1-logcat-race`) is harness-only;
Activity launched COLD then stopped before X start. Not a product result.

Fresh cell `r1-proto0-oracle/`: PROTO=0 TELEMETRY=1. X PID **21639** appeared,
socket ready, then died before holder.

Launcher `x3-launcher.raw.log`:

```text
Uctx signo=11 si_code=1 si_addr=0x0000000000000000 PC=0x000000004800229c
Upid pid=21639 tid=21639
Ssig signo=11 code=1 addr=0x0000000000000000 (rt_sigaction+ucontext)
```

`PC=0x4800229c` is the same 0x4800xxxx class as historical `15caa00` Uctx
parse (not a proven instruction pointer). `Uraw` is captured. Debuggerd
`Fatal signal` line was not in the filtered logcat window.

Stable 16085 throughout. Experimental force-stopped after the cell.
`NO_X3_RESIDUE`.

This is **NEW versus 88e3f17**, where PROTO=0 oracle/stress passed (X 19530).
Do not treat it as the 88e3f17 x-ready-timeout. Do not overwrite this cell.

Evidence: `r1-proto0-oracle/`.

## R1 PROTO=0 rerun — PASS (21639 NON-REPRODUCED)

User-authorized one bounded rerun only (historical 21977 non-repro pattern).
Fresh cell `r1-proto0-oracle-rerun1/`. Did not overwrite the first crash cell.

| | |
|---|---|
| serial | `10.193.235.219:38663` live-fetched |
| Activity | COLD, displayId=0, `com.waydefu.x11gpu` |
| X | PID **27435** `termux-x11gpu com.waydefu.x11gpu :3` |
| oracle | 1514 fail=0 maxΔ=0 Xnz=0 exact_px_acc=1396616 ±1_px=0 |
| stress | 100/100, mixed 100/100, 1000/1000, X alive |
| GATEA_EVENT | 0 |
| GATEA_BIND | Activity 19429 version=0 bound=0 |
| launcher Uctx | NONE |
| exit | 0 in 73055 ms |
| lastUpdateTime | 2026-09-15 01:23:15 unchanged |
| Stable | 16085 |
| residue | `NO_X3_RESIDUE` |

Harness leftover: `STOP logcat pid 27390 still alive after TERM`; post-check
`STILL_ALIVE=no`. Not a product result.

Classify PID **21639** as OBSERVED then **NON-REPRODUCED** on this one retry.
Forensics: `r1-proto0-oracle/GATE-A-P2-R1-PROTO0-21639-FORENSICS-20260915.md`.
PC `0x4800229c` is inside `dalvik-jit-code-cache`. Same register/Uraw-60
family as PID **21977**. Root cause **NOT PROVEN**. Source fix **not**
authorized. R3 later PASSed on PROTO=1 and does not clear this packet.

Evidence: `r1-proto0-oracle-rerun1/`.

## Not run from R1

- R2
- R4–R10
- T2 6/6
- Production enable
