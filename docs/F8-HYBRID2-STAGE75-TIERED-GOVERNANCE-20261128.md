# Stage 7.5 tiered governance — architecture, audit and fixes

Code candidate `f538cb4b7781d9e4cdda85f6659efcc6e1b4021f` (scripts `f8_hybrid2_*`; later commits change only test tooling and docs). Acceptance rules: [freeze](F8-HYBRID2-STAGE75-TIERED-FREEZE-20261128.md). Device results: see the Stage 7.5 tiered report in the evidence tree (results table below).

## One governor, four modes

`scripts/f8_hybrid2_budget.py` owns every governed quantity. A mode is one `Profile` row; nothing else is duplicated.

| Quantity | Where enforced | 2 | 4 | 6 | 8 |
|---|---|---:|---:|---:|---:|
| Relay leases (= independent relay clients) | `acquire_lease`, flock `slot-i` | 2 | 4 | 6 | 8 |
| Daemon sessions | daemon `max_clients = mode` | 2 | 4 | 6 | 8 |
| Group tool executions (daemon native + relay local/fallback) | flock `exec-i`, shared across PRoot and native | 2 | 2 | 1 | 1 |
| Queued + running native calls per relay/session | relay `native_pending`, daemon `session_queue` | 4 | 4 | 4 | 4 |
| Local workers per relay | relay | 1 | 1 | 1 | 1 |

Client count and execution count are separate quotas: an idle relay costs one lease and its interpreter; work costs an execution slot wherever it runs.

The budget directory stores the mode (`f8_hybrid2_budget.py init DIR --mode N`). `init` takes every lock first and refuses while any participant is alive; admission re-reads the mode after locking. Leases and execution slots are kernel flocks, released by process exit.

### Byte and parse limits (budget mode)

| Limit | Legacy | Budget mode | Why |
|---|---:|---:|---|
| Request frame | 4 MiB | 512 KiB | Requests to the four tools are small; parse cost dominates. |
| Parse cost per frame (`parse_cost`) | — | 2 MiB | `json.loads` of a container-dense 1 MiB frame needs ~26 MiB (measured); the estimate is a tracemalloc-calibrated upper bound. |
| Admitted requests per session | — | one 2 MiB parse budget | Queued requests keep their parsed params. |
| Response frame at relay | 16 MiB | 2 MiB + 64 KiB | Tool text ≤ 1 MiB; re-escaping inner JSON at most doubles it. Error echoes are shorter than the request frame. |
| Relay stdout / stdin-to-UDS watermarks | 8 / — MiB | 256 / 256 KiB | Backpressure instead of buffering. |
| Daemon output | close at 16 MiB | worker waits up to the default timeout at 2 MiB + 64 KiB | Slow reader gets backpressure, not a dropped session. |
| `python_json_summary` parse cost | — | 24 MiB | A 16 MiB JSON document could need ~480 MiB of objects. |
| git | default threading | `core.preloadIndex=false`, `index/grep/pack.threads=1` | One task per child; output unchanged. |

### Scheduling

Daemon (budget mode): a `tools/call` beyond free execution slots waits in its session queue. A single dispatcher path (`pump`) starts requests round-robin across sessions and skips a session whose output buffer is above the watermark. Queued requests time out with `-32001 Request timed out before execution`, are dropped silently on cancellation, and are discarded when the session closes. Slots freed by relay-local work are noticed by a 20 ms accept-loop poll while requests wait. Relay local and fallback workers poll for a slot every 20 ms until their deadline. Cross-process fairness between the daemon and relay-local waiters is not FIFO.

## Audit findings and fixes

| # | Finding | Effect before | Fix | Modes |
|---|---|---|---|---|
| F1 | Selective relay kept reading stdin while bytes for the daemon accumulated; at 8 MiB it set `stop` without a reply | Legal native traffic could end the session silently | stdin interest off while `to_uds ≥ watermark` | both |
| F2 | Valid JSON rejected by `json.loads` with `ValueError` (integers > 4,300 digits) or `RecursionError` was not caught (only `JSONDecodeError`) | Relay main loop crashed; daemon session thread ended | catch `ValueError`/`RecursionError` → `-32700` | both |
| F3 | Daemon worker `Thread.start` failure re-raised out of `serve()` | Session died with every outstanding request | `-32000` reply, capacity released | both |
| F4 | Parse expansion: a 4 MiB frame of `{}` costs ~100 MiB in relay and again in the daemon | One client could push the group past its budget | `parse_cost` gate, per-session retained budget | budget |
| F5 | JSON summary parsed up to 16 MiB documents in-process | ~30× expansion | 24 MiB parse-cost cap (`json-parse-budget`) | budget |
| F6 | Text search built `text.splitlines()` for a whole 2 MiB file | ~40 MiB for short lines | bounded segments, identical line numbering (property test) | both |
| F7 | Daemon closed a session when a slow reader let output exceed 16 MiB | Completed results lost | bounded wait in budget mode | budget |
| F8 | Executions limited per process only; relay-local work was outside any group count | N relays × local workers + daemon workers | group `exec-i` slots | budget |
| F9 | Over-capacity calls were refused immediately | Busy errors under normal multi-client load | per-session queue + round-robin | budget |
| F10 | git preload/grep threads scale with CPUs | Thread count per child not one | single-thread git config | budget |
| F11 | Selective relay held separate signal and wake pipes | 2 extra FDs per relay | one wake pipe (kept registered while stdout is paused) | both |
| F12 | Measurement tooling read `/proc/PID/task/TID/children`, absent on this kernel | Earlier "observed descendants" peaks excluded every git/regex child | PPID scan of `/proc/*/stat` | tooling |

Negative controls: reverting F1, F2 or F11 turns the corresponding new test red.

## What is and is not a hard limit

- **Cooperative (this code)**: leases, execution slots, queues, byte and parse limits. They bind processes that share the same budget directory and environment. Another directory, a direct socket client or a program launched without the variable is outside them.
- **Kernel-enforced, used**: flock release on process exit; the daemon's own pidfile flock.
- **Not available or not used**: no cgroup on non-root Android; `RLIMIT_NPROC` counts the whole app UID; `RLIMIT_AS`/`RLIMIT_DATA`/`RLIMIT_NOFILE` are per process and inherited by git, so they would cap a child at the group size rather than its share. `/proc/pressure` is not readable here.
- **Bounded by measurement only**: git child working set (no code limit), `os.walk` per-directory listing size (filesystem-dependent), CPython allocator retention.

## Remaining limits

- Modes 6 and 8 exceed 256 MiB in the theoretical sum even with one execution slot (idle interpreters plus enforced buffers); see the results table.
- A stalled reader can hold an execution slot for up to the default timeout (30 s) before its session is closed.
- Deep JSON nesting between ~10,000 and ~15,600 levels parses on CPython 3.14 (native) but raises `RecursionError` on 3.12 (PRoot); the 2 MiB parse budget rejects deeper input in both.
- Rollback: unset `F8_HYBRID2_BUDGET_DIR` (legacy limits, ungoverned) or `F8_NO_HYBRID=1` (PRoot-only); nothing is deployed.
