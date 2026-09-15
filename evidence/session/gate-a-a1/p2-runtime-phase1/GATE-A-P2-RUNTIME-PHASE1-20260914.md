# GATE A P2 Runtime Qualification — Phase 1 (2026-09-14)

Authority: user-authorized R0→R1→R2→R3 only. Production source not modified.
Worktree `/root/projects/GPU加速/src/f8-ahb-gatea-a1` HEAD
`15caa00908aa9d1f1c4a78bb630aa24a93e7e4cd` remained CLEAN.

## Result

```
R0 PASS
R1 OFF unset PASS
R1 OFF =0 FAIL — NEW SIGSEGV observation, PID 31807
R2 NOT RUN
R3 NOT RUN
P2 RUNTIME PHASE 1 FAIL
Production Gate A BLOCKED
```

Stopped immediately after R1-B. No retry. No R4–R10. No source repair.

## Artifact / device

- APK SHA256 `d69aff2c98d6a3442ff11151ba5858ef6b9537663a94b2f62302766da94f0e8d`
- package `com.waydefu.x11gpu` versionName `1.03.01-15caa00-13.09.26` versionCode 15
- installed libXlorie.so Build ID `33a3b67f3c4213a1611f1fcb18232f2acb2f9d79` MATCH
- device `10.193.235.219:35301` product `myron` model `25102PCBEG` Android 16 / SDK 36
- GLES `Adreno (TM) 840`
- Stable `:1` PID **16085** `termux-x11 com.termux.x11 :1 -legacy-drawing` unchanged throughout
- HDMI: observed pre-existing Stable `com.termux.x11` on Display #3; **zero HDMI operations**; experimental launched `--display 0` only

## R1-A (PROTO unset, TELEMETRY=1)

X PID **27873** ppid=1. Oracle `1514 fail=0 maxΔ=0 Xnz=0`. Stress x100/mixed100/x1000 all fail=0 alive=1.
Gate A `GATEA_EVENT` count **0**. No fatal during this session. Teardown `NO_X3_RESIDUE`.

## R1-B (PROTO=0, TELEMETRY=1) — FAIL

Fresh activity display 0 RESUMED/reportedDrawn=true. X PID **31807** started, unix `:3` appeared, then died before holder connect.

P2-A.3 handler (`InitOutput.c:378` `p2a3CrashHandler`, unstripped `+0xeea70`):

```
signo=11 si_code=1 si_addr=0x0
PC=0x48000ec4 LR=0x6d2bd2b8e0
PID=31807 TID=not captured
Build ID=33a3b67f3c4213a1611f1fcb18232f2acb2f9d79
generation/serial=none (no GATEA_EVENT)
```

Backtrace frame 1 is the crash **handler**, not the original fault (same class as historical A1 handler-epilogue limitation). debuggerd tombstone **not** written for this PID (latest tombstones remain 2026-09-13 17:57).

Classification: **NEW OBSERVATION**. Historical A1 SIGSEGV remains OBSERVED / NON-REPRODUCED / ROOT CAUSE UNKNOWN. This PID 31807 event is not merged into “fixed”.

Evidence:

- `r1-eq0/x3-launcher.raw.log`
- `r1-eq0/p2a3-last-uctx.txt`
- `r1-eq0/addr2line-eea70.txt`
- `r1-unset/oracle.out` `x100.out` `mixed100.out` `x1000.out`

## Stop

No R2 imported-AHB fixture was executed. No R3 direct transaction. Experimental force-stopped; `NO_X3_RESIDUE`; Stable PID 16085 unchanged.
