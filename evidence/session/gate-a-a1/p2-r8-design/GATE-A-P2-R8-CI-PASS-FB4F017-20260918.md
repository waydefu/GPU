# GATE A P2 R8 CI PASS — fb4f017 / 35338856846 — 2026-09-18

```
STATUS: R8_CI_PASS
        first NEW CI after fb4f017 test-only Terminate → GiveUp(0)
        not a rerun of 35304122983 / 35305368742 / 35311343984 /
        35321447455 / 35331185799
        Production Gate A BLOCKED
```

| Field | Value |
| --- | --- |
| Local SHA | `fb4f017c73e942e13dc2423744acb912c055b74e` |
| Parent | `2a245b0bc5d38394df29546e0af0de798f9d260c` (unamended) |
| Remote fork SHA | `fb4f017c73e942e13dc2423744acb912c055b74e` |
| CI run | **35338856846** |
| Event | `workflow_dispatch` |
| headSha | `fb4f017c73e942e13dc2423744acb912c055b74e` |
| Conclusion | **success** |
| Job | Build `105579922097` success |
| URL | https://github.com/waydefu/termux-x11/actions/runs/35338856846 |

Local SHA = remote SHA = CI headSha. Frozen runs not rerun.

## Native compile

`lorie_r8_test.c` compiled. `FAILED:` count in job log = 0. `ninja: error` count = 0.

Unstripped arm64 `ddxGiveUp` still calls `lorieR8ObsEnd` then `exit`.
Opcode 3 in `ProcLorieR8Dispatch` calls `WriteToClient` then `GiveUp@plt`.
`GiveUp` ORs `dispatchException` with `#0x2` (`DE_TERMINATE`).
