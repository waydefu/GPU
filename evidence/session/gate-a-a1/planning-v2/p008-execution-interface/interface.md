# V2-P008 — C1 EXECUTION INTERFACE BIND

PACKET      V2-P008-C1-EXECUTION-INTERFACE-BIND
DATE        2026-09-21
MODE        HOST-ONLY / READ-ONLY / NO DEVICE MUTATION / NO GRANT CONSUMED
VERDICT     INTERFACE_BOUND (with 2 residual documentation gaps, both NON-BLOCKING)
CLOSES      GAP-6 · D-15 · §22.7 step 5/6/7

## 1. Runner interface — the plan's form was WRONG

```
PLANNED (V2.2 §22.7 step 5, marked PROPOSED):
    bash run-r8-one-cell-b984ded-v2.sh --cell c1 --attempt 09 --serial "$SERIAL"

ACTUAL (source-read, run-r8-one-cell-b984ded-v2.sh L32-L47):
    CELL_ID=R8-C1 EVIDENCE=<abs dir> SERIAL=<serial> \
      bash run-r8-one-cell-b984ded-v2.sh
```

The runner parses **no command-line flags at all**. It is environment-driven.
Per §22.7's own rule ("flag 名稱必須先對 runner 真實介面確認。不符 -> BLOCKED + STOP,
不得自行改 flag"), the planned command would have produced BLOCKED. Binding it here
is what P008 exists to do; this is not a self-modified flag.

### Required environment
| var | required | notes |
|---|---|---|
| `CELL_ID` | YES | closed vocabulary, see below. Missing -> `R8_BLOCKED CELL_ID` (exit 3) |
| `EVIDENCE` | YES | absolute dir. **MUST NOT already exist** -> `R8_BLOCKED evidence_exists` |
| `SERIAL` | YES unless VALIDATE_ONLY=1 | missing -> `R8_BLOCKED SERIAL` |
| `VALIDATE_ONLY` | no (default 0) | `1` prints `R8_LIVE_RUNNER_B984DED_V3_VALIDATE_ONLY <cell>` and exits 0 with **zero device mutation** |

### CELL_ID vocabulary (exact, case-sensitive)
```
R8-C1  R8-C2  R8-C3-window  R8-C3-disconnect  R8-C4
R8-C5-full  R8-C5-overflow  R8-D  R8-P1  R8-P2
```
Anything else -> `R8_BLOCKED bad_cell <value>`.
**The plan's lowercase `c1` is not accepted.** All ten plan cell names must be
rewritten to this vocabulary before use.

### Exit codes
```
3  R8_BLOCKED  refuse()   -- infra/preconditions; attempt NOT CONSUMED
2  R8_INVALID  invalid()  -- run started but evidence unusable
*  judge rc passed through (written to $EVIDENCE/judge.rc)
```

## 2. VALIDATE_ONLY is a genuine zero-mutation dry run
`VALIDATE_ONLY=1` returns at L41-L44, **before** the `SERIAL` check, before
`adb_or_block`, before `mkdir -p "$EVIDENCE"`. It validates only CELL_ID and
EVIDENCE presence. It is therefore safe to run with no device attached and
cannot consume an attempt. Recommended as the first step of any C1 grant.

## 3. Canonical ADB form (harness-lib.sh L15-L19) — corroborates V-7R
```bash
ADB() {
  env -u ADB_SERVER_SOCKET -u ANDROID_ADB_SERVER_ADDRESS -u ANDROID_ADB_SERVER_PORT \
    HOME=/data/data/com.termux/files/home ANDROID_NO_USE_FWMARK_CLIENT=1 \
    /data/data/com.termux/files/usr/bin/adb -H 127.0.0.1 -P 5038 -s "$SERIAL" "$@"
}
```
Three independent points:
1. The harness already uses `-P 5038`, never the env var -> V-7R confirmed by tooling.
2. It **actively unsets** `ANDROID_ADB_SERVER_PORT`. The V2.1/V2.2 prescription
   `ANDROID_ADB_SERVER_PORT=5038 adb ...` was not merely weaker on provenance, it was
   **incompatible**: the runner would have scrubbed it.
3. It pins `-H 127.0.0.1` alongside `-P 5038`. The bound form is
   `adb -H 127.0.0.1 -P 5038 -s "$SERIAL"`, not bare `-P 5038`.
4. `HOME` and `ANDROID_NO_USE_FWMARK_CLIENT=1` ARE set by the harness for its own
   adb calls (incl. the long-running logcat stream). They must not be blanket-denied
   in ENV_DENYLIST; the denial applies to the packet operator's shell, not the harness.

## 4. collect / judge / orchestration are invoked BY the runner
```
L329  python3 $COLLECT --raw <ev>/collect-input.txt --out-x <ev>/x-observations.jsonl \
                       --out-r <ev>/renderer-observations.jsonl --completeness <ev>/completeness.json
L449  python3 $ORCH   wait-finalized --cell $CELL_ID --evidence <ev> --deadline-s 8
L453  python3 $ORCH   scan --raw <ev>/raw-logcat.txt --raw <ev>/gatea-ring.txt \
                           --raw <ev>/gatea-summary.txt --out <ev>/producer-scan.json
L491  python3 $ORCH   permit-judge --cell $CELL_ID --evidence <ev> --shutdown-requested <v> \
                           --fixture-alive <v> --fixture-killed-by-runner <v> --x-alive-after-construction <v>
L502  python3 $JUDGE  --manifest <ev>/manifest.json --spec $SPEC --evidence <ev> \
                           --cell $CELL_ID --output <ev>/judge.json
L86   python3 $ORCH   emit-state --file <ev>/orchestration-state.jsonl --state <STATE>
```
**Therefore §22.7 steps 6 and 7 (operator calling collect-r8.py and judge-r8-v2.py
separately) are redundant and must be removed.** Calling them by hand would
double-write evidence and is a corruption risk.

## 5. Path binding — `HERE` is hardcoded, and the plan does not record it
```
HERE         = /root/projects/GPU加速/src/f8-ahb-gatea-r7-p1-arm/tests/r8
               -> SPEC, JUDGE, COLLECT, ORCH all resolve here
ROOT_HARNESS = evidence/session/gate-a-a1/p2-r3-terminal-runtime   (harness-lib.sh)
RUN          = evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
MANIFEST     = evidence/.../p2-r8-runtime/runtime-b984ded/r8-runtime-tooling-manifest-v2.json
FIXTURE      = /tmp/p_r8_lifecycle      (sha checked against EXPECT_FIXTURE_SHA)
```
All four repo paths verified present 2026-09-21. §2.3 records only
"Runner 路徑前綴 = evidence/.../p2-r8-runtime/" and does NOT record that every other
tool resolves through a hardcoded worktree path. If that worktree is pruned or moved,
the runner fails mid-run. Both prefixes must be pinned.

**`FIXTURE=/tmp/p_r8_lifecycle` is in tmpfs.** It does not survive reboot. Preflight
must confirm it exists and matches `ad93f2ba…f12de` before any grant, or the run dies
at L98 with `R8_BLOCKED fixture_sha`.

## 6. Tooling hash reverify (V2-P003 folded in, 2026-09-21)
8 of 8 checkable authority hashes MATCH. See ../p003-tooling-hash/ for the table.

Two residual gaps, both NON-BLOCKING for C1:
- **G1** §2.3 pins FIXTURE ELF `ad93f2ba…` and FIXTURE SOURCE `f6f6a740…` but gives no
  filenames, so they cannot be reverified from the plan alone. The runner checks the
  ELF itself at L98, so C1 is protected; the plan text is what is incomplete.
- **G2** `evidence/.../p2-r8-runtime/r8_orchestration_v2.py` (`21f97d9f…`, 09-18 14:51)
  is a **stale sibling copy that is NOT on the execution path** (HERE points elsewhere).
  Anyone hashing "the file next to the runner" gets a MISMATCH and may wrongly declare
  tooling corruption. It also encodes the OLD terminal model
  (`"signal":"SIGTERM"` / `OsSignal(SIGTERM, GiveUp)`) whereas the authority copy
  encodes `"control":"LORIE-R8-TEST Terminate opcode 3"` / `ProcLorieR8Terminate`
  -- consistent with P007 RULING-4. Recommend marking it stale in place; do not delete
  (append-only evidence).

## 7. Bound C1 command set
```
1  PREFLIGHT   assert SERIAL appears verbatim in:
               adb -H 127.0.0.1 -P 5038 devices            (V-23 / R-27)
2  EXISTS_EXEC adb -H 127.0.0.1 -P 5038 -s "$SERIAL" shell getprop ro.product.device
3  EXISTS_EXEC adb -H 127.0.0.1 -P 5038 -s "$SERIAL" shell dumpsys package com.waydefu.x11gpu
4  EXISTS_EXEC sha256sum <the 6 tooling files at their bound paths>
5  EXISTS_EXEC CELL_ID=R8-C1 EVIDENCE=<attempt-09 dir> VALIDATE_ONLY=1 \
                 bash run-r8-one-cell-b984ded-v2.sh          # zero-mutation dry run
6  GRANTED     CELL_ID=R8-C1 EVIDENCE=<attempt-09 dir> SERIAL=<serial> \
                 bash run-r8-one-cell-b984ded-v2.sh          # THE attempt-consuming call
7  EXISTS_EXEC sha256sum <attempt-09 dir>/* > <attempt-09 dir>/sha256sums.txt
   (former steps 6/7 collect/judge REMOVED -- runner calls them internally)
```
