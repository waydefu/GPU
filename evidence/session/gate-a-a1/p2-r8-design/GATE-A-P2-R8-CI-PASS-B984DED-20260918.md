# GATE A P2 R8 CI PASS — b984ded / 35347497216 — 2026-09-18

```
STATUS: R8_CI_PASS
        first NEW CI after b984ded libxcb extension-minor sender
        not a rerun of 35304122983 / 35305368742 / 35311343984 /
        35321447455 / 35331185799 / 35338856846
        Production Gate A BLOCKED
```

| Field | Value |
| --- | --- |
| Local SHA | `b984dedcac731b77ca4cf8899f8a78b7848ad083` |
| Parent | `fb4f017c73e942e13dc2423744acb912c055b74e` (unamended) |
| Remote fork SHA | `b984dedcac731b77ca4cf8899f8a78b7848ad083` |
| CI run | **35347497216** |
| Event | `workflow_dispatch` |
| headSha | `b984dedcac731b77ca4cf8899f8a78b7848ad083` |
| Conclusion | **success** |
| Job | Build `105607399196` success |
| URL | https://github.com/waydefu/termux-x11/actions/runs/35347497216 |

Local SHA = remote SHA = CI headSha. Frozen runs not rerun.

## Native compile

`lorie_r8_test.c` compiled. `FAILED:` count in job log = 0. `ninja: error` count = 0.

This commit is host fixture/runner only. Unstripped arm64 Build ID remains
`3658dd1f8047bfbb9d4671b269305313adaf1aa7` (same native object as `fb4f017`).

Unstripped `ddxGiveUp` still: `CloseWellKnownConnections` → `UnlockServer` →
`lorieR8ObsEnd` → `exit`.

Opcode 3 in `ProcLorieR8Dispatch`: `lorieR8Obs` → `WriteToClient` → `GiveUp@plt`.

`GiveUp`: `orr w10, w10, #0x2` (`DE_TERMINATE`).
