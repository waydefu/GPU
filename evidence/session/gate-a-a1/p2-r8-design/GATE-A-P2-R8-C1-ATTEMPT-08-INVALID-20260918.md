# GATE A P2 R8-C1 attempt-08 INVALID — 2026-09-18

```
STATUS: R8_INVALID JUDGE_NOT_PERMITTED / MULTI_BEGIN_x
        GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13
        b984ded INSTALLED CI 35347497216
        C1 attempts 01–08 FROZEN
        C2–P2 NOT RUN
        Production Gate A BLOCKED
```

Do **not** retry C1 attempts 01–08. Do **not** start R8-C2 or R9.
Do **not** rerun CI 35304122983 / 35305368742 / 35311343984 / 35321447455 /
35331185799 / 35338856846 / **35347497216**.
Do **not** amend b984ded / fb4f017 / 2a245b0 / 5a782f6 / 65938a4.

## Bind

| Field | Value |
| --- | --- |
| SERIAL | `192.168.1.100:46715` |
| source | `b984dedcac731b77ca4cf8899f8a78b7848ad083` |
| parent | `fb4f017c73e942e13dc2423744acb912c055b74e` |
| CI | **35347497216** |
| versionName | `1.03.01-b984ded-18.09.26` |
| APK SHA256 | `0d06de68025ca41d91e316d55f6f77ba9d5b3ba1a90b6a2bfacb65add0d398d3` |
| Build ID | `3658dd1f8047bfbb9d4671b269305313adaf1aa7` |
| X | PID **29598** `termux-x11gpu com.waydefu.x11gpu :3` |
| renderer | PID **1563** |
| Stable | PID **20146** `1.03.01-11b82d9-06.09.26` lastUpdateTime 2026-09-07 22:55:03 UNCHANGED |
| cell | `p2-r8-runtime/runtime-b984ded/r8-c1/attempt-08-xcb-sender/` |
| runner | `p2-r8-runtime/run-r8-one-cell-b984ded.sh` SHA256 `f22546b7…ab7b0` |
| fixture | `/tmp/p_r8_lifecycle` SHA256 `ad93f2ba…12de` |

Install **PASS** (`runtime-b984ded/r0/`, `pm-install-commit.raw.txt` Success).

## Observed (xcb sender DID dispatch)

- `CLIENT_OK`; `TERMINATE_SENT`; `FAIL r8 request minor=3 no_reply seq=32`; `X_HANGUP_AFTER_TERMINATE`; fixture exit **0**.
- Server-side `"phase":"TEST_CONTROL"` `"op":"TERMINATE"` **PASS** (X seq 38).
- `ddxGiveUp` flight dump 21:11:20.379 then X `END` seq 45 `actual_count=45`.
- Renderer `R_UNBOUND_FINAL` then `END` seq 7 `actual_count=7`.
- Completeness jsonl: X BEGIN=1 END=1 n=47; renderer BEGIN=1 END=1 n=9.
- `wait-finalized` **FINALIZED ok**. producer-scan raw-only `x_begin=1 x_end=1 r_begin=1 r_end=1`.
- No `R8_OBS_POST_END`. No second `InitOutput` generation.
- Judge **not invoked**. `permit-judge` **REFUSE MULTI_BEGIN_x** → `R8_INVALID JUDGE_NOT_PERMITTED`.

## Classifier

`R8_INVALID JUDGE_NOT_PERMITTED` / `MULTI_BEGIN_x`.

Class: **TEST CONSTRUCTION / ORCHESTRATION**. `permit_judge` concatenates
`scan_files(raw-logcat + ring + summary + x3-launcher)` with collector
`x-observations.jsonl`, so the same producer BEGIN is counted twice.
Raw-only scan and jsonl-only each have BEGIN=1.

The libxcb extension-minor sender reached `ProcLorieR8Terminate` / `GiveUp(0)` /
`ddxGiveUp` / X END. That attempt-07 hole is closed. This cell is still INVALID
because the live runner refused the judge.

Do **not** move X END. Do **not** enable product `-terminate`. Do **not** SIGKILL.
Do **not** silent-retry this cell. Do **not** start C2.
