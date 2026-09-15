# Gate A P2 R6 design-complete runtime — 9369553 — 2026-09-15

Install of `9369553` **DONE**. **R6-D1 PASS** (`r6-d1-retry5`). First D2-INFLIGHT **FAIL** (kept). Fixture `ASYNC|COPY` retry1 **FAIL** (reject PROVEN; EVENT_COMPLETED serial 6 ABSENT). **D2-OOM NOT RUN**.
D2 COMPLETED root cause **PROVEN**; source telemetry `54ff35b` is **not** this APK and is **HOLD (do not push)**. Packets:
`../../p2-r6-design/GATE-A-P2-R6-D2-COMPLETED-ROOT-CAUSE-20260915.md`,
`../../p2-r6-design/GATE-A-P2-R6-D2-HOLD-20260915.md`.
Do not overwrite historical D1 cells, `r6-d2-inflight/`, or `r6-d2-inflight-retry1/`. Do not silent-retry these cells. Do not start R7.
Stable `:1` package UNTOUCHED (`1.03.01-11b82d9-06.09.26`). Current X PID **1004** (was 16085 at install). Production Gate A remains **BLOCKED**.

## Binding

| | |
|---|---|
| serial | `10.193.235.219:33851` live-fetched `_adb-tls-connect._tcp.local.` |
| Installed | `com.waydefu.x11gpu` `1.03.01-9369553-15.09.26` CI **34926730189** |
| APK SHA256 | `02baccbfd745dffcaa62699452c386710d5a7cf1b63217ea293141e06d98af7f` MATCH |
| Build ID | `82136dd9ebd230b8bf6d655f334ac40e4be998a8` MATCH |
| HEAD | `936955397619091b48c8e717f28b2cd187d79065` |
| Stable | `com.termux.x11` `1.03.01-11b82d9-06.09.26` lastUpdateTime 2026-09-07 22:55:03; PID **1004** at retry (PID **16085** at install) UNTOUCHED |
| HDMI | observe-only, `mDisplayId=0` |

Install cell: `r0/INSTALL-9369553-20260915.md`.

Fixtures (host `cc`, SHA recorded in cells):

| | source | ELF |
|---|---|---|
| `p_r6_d1_queued` first | `da5ff4be…5d2a` | `286e6ce4…b2c4` |
| `p_r6_d1_queued` retry1 | `0ed73a07…6d88` | `86143cc0…82d6` |
| `p_r6_d1_queued` retry2 | `9b6834ba…14c2` | `63433803…70a8` (PolyFill onto `copypm`, not dest) |
| `p_r6_d1_queued` retry4 | `3ca2f77c…bf91` | `8a3b8509…a953` (CreateGC on B after A pixmap sync) |
| `p_r6_d1_queued` retry5 | `7d147aff…a774` | `e74776f3…1197` (Present `ASYNC\|COPY` + PutImage presentpm) |
| `p_r6_d2_present` first inflight | `3fe0ba7d…a425` | `7052a358…9bf8` |
| `p_r6_d2_present` retry1 | `6b7e8277…4ec8` | `ffce3910…b068` (`ASYNC\|COPY`) |
| `p_r6_d2_present` post-retry1 (host only; not run on this APK) | `c4e8a680…3c9a` | `2ca0957f…68a3` (CompleteNotify after immediate Composite) |

D1/D2 sources were aligned before the cell: D1 pixel check after Composite reply; D2 Composite picture on the Present window. `p_r6_cross_op.c` was not edited.

## R6-D1 — FAIL

| | |
|---|---|
| Command | `SERIAL=… VARIANT=d1 CELL=…/runtime-9369553/r6-d1 bash run-r6-design.sh` |
| Script exit | **2** `R6_DESIGN_FAIL fixture_rc` |
| Activity | COLD Display0 `GATEA_BIND` nonce=`10181545525639370984` |
| X `:3` | PID **24748** ALIVE then torn down |
| Env | `TERMUX_X11_GATEA_PROTO=1` `TELEMETRY=1`; OOM hook **unset** |
| Fixture | `FAIL D1-composite-dst pixels fail=1 maxΔ=64 got0=00800000 expect=00804000` |
| Fatal | none |
| Teardown | `STABLE 16085` `NO_X3_RESIDUE` |
| GATEA | 67 lines, max_seq=66 (&lt; 512), firstFailed=0, overflow not indicated |

REQUEST_ARRIVED (29) majors decoded from `src`:

```text
seq 15 CopyArea          (62)
seq 18 PolyFillRectangle (70)
seq 25 GetImage          (73)
seq 27 PresentPixmap     (146.1)
seq 28 Render Composite  (138.8)
```

Composite CALLBACK xop=3 is seq 29. PUBLISH/COMPLETED/SUCCESS serial **7** at seq 38/43/44.

**OBSERVED:** client-2 Copy/Solid/GetImage REQUEST_ARRIVED and CALLBACK run **before** the in-flight Composite REQUEST. The D1 “second op queued behind `DoneComposite` wait” schedule was **not constructed**. Pixel oracle then saw 1/64 pixels still `00800000` (unblended dst) vs `00804000`.

**NOT PROVEN:** X-client pump inside `gateAWaitTerminal`. Events 29–30 **did emit**.

## R6-D1-retry1 — FAIL (schedule constructed; pixel oracle)

Authorized 2026-09-15: fixture/schedule only. Device stayed `9369553`. First cell `r6-d1/` not overwritten.

| | |
|---|---|
| Fixture ELF | `86143cc0…82d6` source `0ed73a07…6d88` |
| Change | XSync both conns after setup; 12 ms in-flight wait; then client 2 |
| Command | `VARIANT=d1 CELL=…/runtime-9369553/r6-d1-retry1` |
| Script exit | **2** `R6_DESIGN_FAIL fixture_rc` |
| X `:3` | PID **22068** ALIVE then torn down |
| Fixture | `D1_SCHEDULE in_flight_wait_ns=12913646` then `FAIL D1-composite-dst fail=1 maxΔ=128 got0=00000001 expect=00804000` |
| Fatal | none |
| Teardown | `STABLE 1004` `NO_X3_RESIDUE` |

REQUEST order (retry1):

```text
seq 19 Render Composite  (138.8)
seq 35 SEMANTIC_SUCCESS  serial=6
seq 44 CopyArea          (62)
seq 45 PolyFillRectangle (70)
seq 50 GetImage          (73)
seq 52 PresentPixmap     (146.1)
```

**PROVEN:** Composite REQUEST before second-op REQUEST. SUCCESS (seq 35) before Copy/Solid/GetImage/Present REQUEST. Wait-pump of those requests is **FALSIFIED** on this cell.

**OBSERVED:** pixel (0,0) is `00000001` = PolyFill fg. After SUCCESS, X dispatched client-2 PolyFill before client-1 GetImage oracle. Not a wait-pump.

**NOT RUN again:** dest-mutating Solid must not race the oracle; that needs a new fixture grant. No silent third D1 of the retry1 ELF.

## R6-D1-retry2 — OBSERVED ART JIT (fixture never ran)

Authorized 2026-09-15: same APK; PolyFill onto `copypm` not dest; then D2 if D1 PASS.

| | |
|---|---|
| Fixture ELF | `63433803…70a8` source `9b6834ba…14c2` |
| Command | `VARIANT=d1 CELL=…/runtime-9369553/r6-d1-retry2` |
| Script exit | **2** `DIED_DURING_8S` |
| X `:3` | PID **28170** died during 8 s socket wait |
| Crash | `signo=11 si_code=1 si_addr=0` PC=`0x48000478` in `[anon_shmem:dalvik-jit-code-cache]` (`48000000-4a000000`) |
| Fixture | **never started** (no pixels, no REQUEST schedule) |
| Fatal in Gate A DDX | **NOT CLAIMED** — ART JIT class |
| Teardown | Stable PID **1004** UNTOUCHED; no experimental `:3` residue |

**OBSERVED:** same family as X 21639 / 21977. Do not patch C for this PC.

**NOT RUN:** D2. Fail-closed: D1 did not complete; no silent-retry of retry2.

Cell note: `r6-d1-retry2/OBSERVED-JIT-20260915.md`.

## R6-D1-retry3 — FAIL CopyArea BadGC (pixels PASS)

Authorized bounded D1 rerun of retry2 ELF. JIT 28170 **NON-REPRODUCED**.

| | |
|---|---|
| Fixture ELF | `63433803…70a8` |
| Command | `VARIANT=d1 CELL=…/runtime-9369553/r6-d1-retry3` |
| Script exit | **2** `R6_DESIGN_FAIL fixture_rc` |
| X `:3` | PID **2555** |
| Fixture | `PASS D1-composite-dst got0=00804000` then `FAIL D1 CopyArea err=13` |
| Schedule | Composite REQUEST seq 19 → SUCCESS seq 35 serial 6 → Copy/Solid/GetImage/Present REQUEST 44–48 |

Official: error 13 = BadGC; `xcb_copy_area` GC must exist; `xcb_create_gc` drawable must exist.
B CreateGC used A's `copypm` before CreatePixmap was processed. retry1 hid this because pixels failed first.

Cell: `r6-d1-retry3/FAIL-COPYAREA-BADGC-20260915.md`.

## R6-D1-retry4 — FAIL missing Present CALLBACK (CLIENT_OK; pixels PASS)

Authorized official-docs fixture fix then one cell. Device stayed `9369553`.

| | |
|---|---|
| Fixture ELF | `8a3b8509…a953` source `3ca2f77c…bf91` |
| Command | `VARIANT=d1 CELL=…/runtime-9369553/r6-d1-retry4` |
| Script exit | **2** `R6_DESIGN_FAIL d1_missing_callback_after_request_present` |
| X `:3` | PID **7648** |
| Fixture | `CLIENT_OK` `PASS D1-composite-dst exact_px=64 got0=00804000` |
| CopyArea BadGC | **FALSIFIED** |
| Wait-pump | **FALSIFIED** (SUCCESS seq 35 then Copy 44 / Solid 48 / GetImage 53 / Present 55) |
| Present CALLBACK xop=4 | **ABSENT** after Present REQUEST |

Source: Present CALLBACK only if `lorieTryScheduleGpuCopy` succeeds (`present_execute.c` ~111–120). Software `present_copy_region` is silent.

Cell: `r6-d1-retry4/FAIL-MISSING-PRESENT-CALLBACK-20260915.md`.

## R6-D1-retry5 — PASS

Authorized scheme A: Present `ASYNC|COPY` + PutImage presentpm. No server C.

| | |
|---|---|
| Fixture ELF | `e74776f3…1197` source `7d147aff…a774` |
| Command | `VARIANT=d1 CELL=…/runtime-9369553/r6-d1-retry5` |
| Script exit | **0** `R6_D1_PASS` |
| X `:3` | PID **16168** |
| Pixels | `got0=00804000` exact 64 |
| Present CALLBACK | seq 60 xop=4 serial=9 after Present REQUEST seq 59; SUCCESS seq 37 serial=6 first |
| Stable | PID **1004** `NO_X3_RESIDUE` |

Cell: `r6-d1-retry5/PASS-20260915.md`.

## R6-D2-INFLIGHT — FAIL missing reject

| | |
|---|---|
| Command | `VARIANT=d2-inflight CELL=…/runtime-9369553/r6-d2-inflight` |
| Script exit | **2** `d2_inflight_missing_reject_reason1` |
| X `:3` | PID **17596** (new PID after D1 teardown) |
| Client | `CLIENT_OK` later pixels `got0=00804000` |
| OOM env | **unset** |

Present REQUEST seq 19 then Composite REQUEST seq 20; Composite SUCCESS serial 6; Present CALLBACK serial 7 **after** that SUCCESS. No event 31.

Cell: `r6-d2-inflight/FAIL-MISSING-REJECT-20260915.md`.

## R6-D2-INFLIGHT-retry1 — FAIL publish before Present COMPLETED

Authorized fixture-only `ASYNC|COPY`. First inflight cell kept.

| | |
|---|---|
| Command | `VARIANT=d2-inflight CELL=…/runtime-9369553/r6-d2-inflight-retry1` |
| Script exit | **2** `d2_lease_or_publish_before_completed` |
| X `:3` | PID **20856** |
| Fixture ELF | `ffce3910…b068` |
| Present CALLBACK | seq 20 xop=4 serial=6 |
| REJECT reason=1 | seq 23 serial=6 **PROVEN** |
| Later PUBLISH | seq 36 serial=8 |
| COMPLETED serial=6 | **ABSENT** (only COMPLETED is serial=8 seq 41) |

## R6-D2-OOM

**NOT RUN.** Fail-closed after retry1 FAIL.

## Classification

| Claim | Label |
|---|---|
| `9369553` installed, SHA/Build ID bound | **PROVEN** |
| First D1 in-flight schedule | **NOT CONSTRUCTED** (`r6-d1/`) |
| Retry1 Composite-before-second REQUEST | **PROVEN** (`r6-d1-retry1/`) |
| Retry1 SUCCESS before second REQUEST | **PROVEN** (wait-pump of D1 ops **FALSIFIED**) |
| R6-D1 client pixels exact | **FALSIFIED** first two cells; **PASS** retry3+retry4+retry5 (`got0=00804000`) |
| Events 29/30 present with TELEMETRY=1 | **PROVEN** |
| Retry2 startup SIGSEGV | **OBSERVED** ART JIT (X 28170); later D1 cells **NON-REPRODUCED** |
| Retry3 CopyArea err=13 | **PROVEN** BadGC; CreateGC-before-pixmap |
| Retry4 wait-pump of second REQUEST | **FALSIFIED** |
| Retry4 Present CALLBACK xop=4 | **ABSENT**; retry5 **PROVEN** (`ASYNC\|COPY`) |
| Design-complete D1 | **PASS** (`r6-d1-retry5`) |
| D2-INFLIGHT reject reason=1 | **ABSENT** first cell; **PROVEN** retry1 |
| Present serial 6 COMPLETED | **ABSENT** on retry1 (event 14 never emitted for legacy COPY on this APK) |
| D2 COMPLETED root cause | **PROVEN** — see `p2-r6-design/GATE-A-P2-R6-D2-COMPLETED-ROOT-CAUSE-20260915.md`; `54ff35b` not installed; **HOLD** `GATE-A-P2-R6-D2-HOLD-20260915.md` |
| Design-complete R6 (all three cells) | **FAIL** (D2-INFLIGHT not PASS; D2-OOM not run) |
| R7 / Production Gate A | **NOT STARTED** / **BLOCKED** |

Evidence: `r0/`, `r6-d1/` … `r6-d1-retry5/`, `r6-d2-inflight/`, `r6-d2-inflight-retry1/`. Do not overwrite.
