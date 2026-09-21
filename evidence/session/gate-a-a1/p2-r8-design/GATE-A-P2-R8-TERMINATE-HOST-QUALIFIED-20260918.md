# GATE A P2 R8 TERMINATE HOST QUALIFIED — 2026-09-18

```
STATUS: R8_TERMINATE_HOST_QUALIFIED
        parent 2a245b0bc5d38394df29546e0af0de798f9d260c unamended
        commit fb4f017c73e942e13dc2423744acb912c055b74e
        Production Gate A BLOCKED
        no device cell in this packet
```

## RCA (source-backed)

| Step | Source | This C1 runtime |
| --- | --- | --- |
| SIGTERM handler | `os/connection.c` `OsSignal(SIGTERM, GiveUp)` | requested after fixture returned |
| `GiveUp` | `os/utils.c` `dispatchException \|= DE_TERMINATE` (`DE_TERMINATE==2`) | not the path that ran first |
| SIGHUP | `AutoResetServer` `DE_RESET` | not used |
| last client | `CloseDownClient` `nClients==0` → `SetDispatchExceptionTimer` | C1 `xcb_disconnect` |
| timer | if `dispatchExceptionAtReset` lacks `DE_TERMINATE`, **immediate** `dispatchException \|= AtReset` | default `AtReset=DE_RESET` |
| `Dispatch` exit | `dispatchException &= ~DE_RESET` | RESET cleared |
| `dix_main` | `ddxGiveUp` only `if (dispatchException & DE_TERMINATE)` | gen-2 `InitOutput` instead |
| X END | `InitOutput.c` `ddxGiveUp` after `UnlockServer` | never reached in attempt-06 |

Product `-terminate` sets `AtReset=DE_TERMINATE`. **Not used.** Product shutdown unchanged.

## Host proof

`python3 tests/r8/verify-r8-support.py` → `R8_SUPPORT_HOST_STATIC_OK`

- terminate → `GiveUp(0)` → no `lorieR8ObsEnd` in the handler
- reset stream without END → `END_COUNT` (not PASS)
- terminate-then-giveup stream → `OK` END exactly once
- post-END producer call → `POST_END` / `R8_OBS_POST_END`
- renderer vectors unchanged
- judge SHA `f021048da3c1b729c6f9bf560eba52609b2f980336dd4fab77ad1700438c0e31`
- collector SHA `e6df519a75c872c8a56fac00146585853eec7f17a3f424e70e5d4736340666c8`

## Frozen C1 history (immutable)

| Attempt | Path | Verdict |
| --- | --- | --- |
| 01–05 | historical | frozen original classifiers |
| 06 | `runtime-2a245b0/r8-c1/attempt-06-giveup-end/` | `R8_INVALID MISSING_END_x` |
| 07 | not created | install BLOCKED `SCREEN_DOZING` |
