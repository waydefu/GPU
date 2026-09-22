# V2-R9-DESIGN — packet 1 of 17

DATE 2026-09-22  MODE design only. No device, no attempts, no runtime.
PRODUCT dc94485 (installed, R8-D and R8-P2 smoke PASS)
PRECONDITION `V2-R8-AGG` PASS — satisfied (12/12).

## §8.6 DELIVERABLES — ALL FOUR NOW EXIST

```
r9-design-freeze.md        -> planning-v2/r9-design-freeze/   9 files, manifest verified
                              Q1-Q11 all resolved, every claim source-cited
r9-identity-contract.json  -> THIS DIRECTORY                  NEW
r9-cell-spec.json          -> THIS DIRECTORY                  NEW
r9-decision-log.md         -> THIS DIRECTORY                  NEW
```
§8.6 says R9 runtime packets stay `BLOCKED` until all four exist. **That gate is now
open.** It is not the only gate; see BLOCKED below.

## WHAT THE FREEZE CHANGED ABOUT R9

The freeze did not merely answer eleven questions. It invalidated part of the packet
design that was written before the answers existed. Five corrections, all recorded in
`r9-cell-spec.json` under `plan_corrections_forced_by_the_freeze`:

```
1  §8.7 #14 V2-R9-RESET           REMOVED. Q10 found the reset already exists, is the
                                  default, and permanently disables Gate A. The packet
                                  can only ever prove the kill, never a recovery.
2  §8.7 common proof item
   "no stale READY consumed"      TAUTOLOGY. Q5 proved it is structurally impossible
                                  (four independent filters). The provable obligation
                                  is that the designed HALT fired.
3  §8.7 WARM-1/2/3 as a uniform
   success chain                  WRONG SHAPE. Q1-F1 makes warm-rebind-over-live-
                                  imports a HALT. The three must differ by TABLE
                                  STATE, not by number.
4  §8.4 WARM/COLD definitions     INCOMPLETE. Q2-F2 proved (nonce, generation) cannot
                                  distinguish them. Activity (PID, starttime) is now
                                  the required discriminator.
5  §8.7 #5/#6/#7 conditional      NO LONGER CONDITIONAL. Done: D-02 needed product
                                  support, dc94485 is built, installed, smoked.
```

## STATUS 2026-09-22 — THE RUNTIME PACKET IS 2 CELLS

> Everything below this banner is the design as frozen on 2026-09-22 morning and is
> kept verbatim as the record of what was designed. Six of the eight cells have since
> been removed as **SOURCE-PROVEN / RUNTIME-NOT-CONSTRUCTIBLE** — not PASS, not FAIL,
> not INVALID, not runtime-qualified — each with a named reopen condition:
>
> ```
> R9-WARM-1/2/3   no product entry point for a warm reconnect/rebind
> R9-COLD-1/3     no drivable published renderer fatal with a TERMINAL registry
>                 (planning-v2/r9-fixture/COLD1-ROUTE-SEARCH.md)
> R9-COLD-2       x-bump-unterminal needs a SECOND lorieActivityConnected() with
>                 generation != 0, and no X process can reach one
>                 (planning-v2/r9-fixture/COLD2-ROUTE-SEARCH.md)
> ```
>
> The `NOT_PROVEN` entries in the table below were therefore right to be honest, and
> the constructibility column is the part of this design that paid for itself: four of
> the four `NOT_PROVEN` cells turned out to be unconstructible, and so did two of the
> four `PLAUSIBLE` ones. **No attempt was burned on any of the six.**
>
> The runtime packet is now `[R9-F1, R9-F2]`; the frozen authority is
> `tests/r9/r9-lifecycle-cell-spec.json` (`R9_CELL_SPEC_FROZEN_V2`).

## THE CELL SET — 8 cells, and an honest constructibility column

```
cell                  grounds        constructibility   expected
R9-WARM-1             Q1, Q4         PLAUSIBLE          PASS
R9-WARM-2             Q1-F1, Q5      NOT_PROVEN *       PASS via expected r-rebind-busy
R9-WARM-3             Q4-F1, Q1-F2   NOT_PROVEN         PASS
R9-COLD-1             Q2, Q2-F1      PLAUSIBLE          PASS
R9-COLD-2             Q2-F1, Q3      NOT_PROVEN         PASS via expected x-bump-unterminal
                                     -> REMOVED 2026-09-22, unconstructible
R9-COLD-3             Q3, Q2-F2      PLAUSIBLE          PASS
R9-F1-STALE-REPLAY    V-11, Q5, Q6   NOT_PROVEN *       PASS via expected fatal
R9-F2-RECOVERY        Q11            PLAUSIBLE          PASS
                                     * the two hardest
```

**Four of eight have unproven construction, and that is the most important output of
this packet.** It is not hedging: §8.8 draws a hard line between
`INVALID_CONSTRUCTION` (the payload never reached the path) and `VALID_FAIL` (it did
and was mishandled). A cell whose construction is assumed rather than proven will
produce the former and burn attempts without evidence. R8 spent nine defects learning
this — four of them found offline at zero cost.

The two hardest, and why:
```
R9-WARM-2  needs the Activity to call connect_ with a NEW fd while the previous X is
           still alive and bound, with a READY import outstanding. connect_ resets the
           socket, the mapping and the legacy buffer lists but NOT gateABound and NOT
           the Gate A tables (activity.cpp:544-550), which is exactly what makes the
           next bind fatal. But the trigger is Java-side
           (MainActivity.tryConnect -> service.getXConnection -> LorieView.connect) and
           the runner has no mechanism for it today.
R9-F1      Q5 and Q6 made this HARDER than V-11 assumed. Every route for delivering
           stale state into the current path is already filtered or fatal: draw-time
           lookup skips foreign tuples, retirement needs an exact triple, rebind over a
           live READY halts, X re-validates per use, and the frame path is fatal on
           mismatch. F1 must find a route that genuinely reaches the current path.
```
Both are inputs to `V2-R9-FIXTURE`. Neither is a licence to run.

## WHAT IS NOW UNBLOCKED

```
V2-R9-FIXTURE (#2)   §8.6 gate satisfied. Its first job is the two NOT_PROVEN
                     constructions above, offline, before any attempt is spent.
V2-R9-JUDGE (#3)     the identity contract defines the fields it must assert, and
                     r9-cell-spec.json defines per-cell expected verdicts including
                     the two expected-fatal cells.
V2-R9-HOST-VERIFY(#4) can be written against #2 and #3 with no device.
#5/#6/#7             DONE (dc94485).
```

## WHAT IS STILL BLOCKED, AND BY WHAT

```
All device packets (#8 onward) are blocked on #4 HOST-VERIFY, per §8.7.
R9-WARM-2 and R9-F1 are additionally blocked on a proven construction.
R9-F2 is blocked on F1 producing its expected fatal — §8.8 forbids manufacturing
  another fatal to satisfy the precondition; without it F2 is BLOCKED, not FAIL.
```

## STANDING OBLIGATIONS FOR EVERY R9 PACKET

```
1  Launch X with -noreset (D-01). Non-negotiable: without it the last X client
   disconnecting silently kills Gate A and every negative observation is unattributable.
2  Record the full per-boundary field set from r9-identity-contract.json, including
   x_fd_table_had_previous_conn_fd read from /proc — Q9-F1 means the product reports
   nothing about the previous fd still being registered.
3  Record BOTH tuple authorities. The renderer admits against its LATCH, never the
   shared field (Q3), and a lag between them is the failure mode.
4  Classify WARM vs COLD from Activity (PID, starttime) only. Never from the launch
   method (§8.4), never from the tuple (Q2-F2), never from the notification-bar Exit
   (V-8).
5  Judge residue against the WINDOWED logcat only (Q11-F2). The obs sink survives
   process death and `logcat -c` is a redline; carry logcat-since.txt.
6  Do not read a missing renderer END as failure without first checking whether
   TERMINATE was sent — the END is now gated on explicit whole-run finalization (D-02).
7  Gate A accelerates only PictOpOver, and a run only took the GPU path if the ring
   contains event=5 — but that rule has three legitimate zero-cases, so compare
   against the cell's own composite count before concluding anything.
```

## WHAT THIS PACKET DOES NOT CLAIM

```
- That any R9 cell will pass. Four of eight have unproven construction.
- That multi-epoch observation works. D-02 makes it POSSIBLE; the smoke proved the
  records exist and are correctly shaped in a SINGLE-epoch run. No test has yet
  crossed a generation boundary with the renderer surviving.
- That the freeze is complete for R10 or Production Gate A. It is scoped to R9.
- Any change to Production Gate A semantics. Nothing in R9's design requires one.
```

## NEXT

`V2-R9-FIXTURE`, starting with the two unproven constructions — offline, at zero
attempt cost, exactly as the four-of-nine R8 defects were found.
