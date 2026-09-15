# Gate A P2 R3 terminal + observability — 2026-09-14

Worktree `/root/projects/GPU加速/src/f8-ahb-gatea-a1`
Commit `88e3f176d5be313b7dee058da9021cfe8d09e7de` on
`qualification/gatea-a1-microprobe-20260912`.
Files: `InitOutput.c`, `lorie.h`, `renderer.cpp` only (+170/−52).

## Cause (source-level; runtime NOT proven)

On `8479997` R3, `GATEA_DRAIN imports=1` ran and X still hit
`x-ready-timeout` with `GATEA_EVENT=0`. That means X received neither
READY nor REGISTER_FAILED. Silent terminals existed in source:

- bound-tuple mismatch released the AHB and returned
- REGISTER_FAILED send failure was log-only (“doomed via HUP”)
- duplicate READY published fatal then returned

Root cause of the `8479997` cell is **still NOT PROVEN**. This change
closes those silent terminals and adds bounded VALIDATE stages so the
next R3 can observe where validate actually stops.

## Change

- Telemetry enable is `LorieGateATelemetry.reserved` (layout unchanged),
  published by X after `lorieGateAProtocolInit`. Default 0 / OFF.
  Renderer/Activity use `lorieGateATelemetryPublished`, never getenv.
- Every dequeued REGISTER ends READY / REGISTER_FAILED / FATAL.
- Failure cleanup remains texture → EGLImage → AHB.
- X waiter last-reads fatal then waiter state before `x-ready-timeout`.
- Queue ABI 168 and P0 sideband 40 unchanged. No ownership/unlock
  reorder, no timeout increase, no CPU/D0a/legacy fallback, no D0b/Gate H.

## Local ARM64 compile

UTF-8 locale + command-local `ANDROID_HOME=/root/android-sdk`.
No `local.properties`. No ASCII symlink. Frozen `GPU??????` log kept.

| | |
|---|---|
| Incremental | exit 0, BUILD SUCCESSFUL 45s, C/C++ compile+link |
| Full-clean | exit 0, BUILD SUCCESSFUL 3m4s, fresh ninja after `:lorie:clean` |
| New warnings | 0 vs 15caa00 / R1 local full-clean fingerprints |
| Verifier | 38/38 GREEN |

Do not install local ninja `.so`.

## CI artifact

Run **34822381586** `workflow_dispatch` success, first attempt,
headSha = `88e3f17`. APK SHA256
`7e5540a247f0a0dd1c179fc818ba2f83abd2d970fb4961588ba6f071b19b8616`.
Build ID `e91c7683b3dd0ac61739f274a5eaeffaace1be12` MATCH.
**NOT INSTALLED.** Runtime not run. Production Gate A BLOCKED.

Authority: `p2-r3-terminal-runtime/HANDOFF-NEXT-AGENT-20260914.md`.
