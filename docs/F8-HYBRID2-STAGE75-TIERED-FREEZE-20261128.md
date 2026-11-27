# Stage 7.5 tiered governance — acceptance freeze (2026-11-28)

Frozen before any device data for the tiered candidate was collected. Code candidate: `03dde1c1e212094d20cc5487179475d0cbd72e78` (scripts only). Any later code change starts a new candidate and a new run directory; results from different candidates are never mixed.

## Scope

Modes 2, 4, 6, 8 (`f8_hybrid2_budget.PROFILES`), each judged independently. Mode 4 is judged first; modes 6 and 8 never block a mode-4 verdict. Measured group = native daemon + PRoot relays + every observed descendant (git, regex worker). Budget directory initialised with `f8_hybrid2_budget.py init DIR --mode N`; daemon and every relay receive the same `F8_HYBRID2_BUDGET_DIR`.

## Cells (per mode, same daemon process unless the cell restarts it)

| Cell | Content |
|---|---|
| C1 normal | N relays, `N*ceil(1000/N)` calls over 60 s, tools cycle tree/search/git/json as in the Stage 7.5 soak; three consecutive cycles. |
| C2 maxload | N relays, each 12 rounds of: 500,000-byte ASCII `ping` frame (largest legal class: < 512 KiB, parse cost < 2 MiB), 12,000-file tree scan, 5,000-match search (1 MiB text result), `git show HEAD -- corpus.txt`, 1.4 MB JSONL summary. |
| C3 overload | N live relays; relay N+1 exits 3 `budget exhausted`; a second daemon exits 3; after one relay exits a new relay is admitted and completes a call. |
| C4 slowread | N relays each send 4 large calls and do not read stdout for 5 s; then all responses are read and checked. |
| C5 lifecycle | per relay: call + `notifications/cancelled` (no reply for it, next call answered); `timeout_s` 0.001 → -32001; half-close with 4 outstanding (4 replies, exit 0); one relay SIGKILLed mid-call. |
| C6 restart/fallback | daemon SIGTERM with N relays connected (pending native calls answered with the disconnect error); N fallback relays without the daemon match the oracle and relay N+1 is refused; daemon restarted; N new relays route natively and match. |
| Drain (after every cell) | daemon threads/FDs equal the post-warm-up idle values; N relay slots and all exec slots acquirable. |
| Soak (mode 4 only) | 600 s continuous C1-rate mixed load. |

## Gates

- **G1 functional**: every reply equals the PRoot local oracle (ungoverned fallback, same SHA) or the error the cell specifies; route log targets match the native tool set; no relay/daemon crash.
- **G2 measured resources**: every 0.2 s sample ≤ 256 MiB PSS, ≤ 64 threads, ≤ 192 FDs. A sample with a restricted /proc read is counted and reported. Host stop gate (cell → INVALID, not FAIL): MemAvailable < 1.5 GiB, CPU > 85 °C or battery > 42 °C.
- **G3 theoretical**: `budget_report(mode)` with measured inputs ≤ 256 MiB, 64 threads, 192 FDs. Inputs: daemon idle PSS (post-warm-up median), relay idle PSS (initialised idle relays / N, median of 3), execution envelope = max tracemalloc peak of one governed tool call on the C2 fixture on either Python × 1.25, child envelope = max sampled PSS of one observed child.
- **G4 RSS (original, unchanged)**: daemon |ΔVmRSS| after drain vs post-warm-up idle ≤ 10 % for every C1 cycle.
- **G5 retained memory (proposal, recorded separately)**: retained = daemon Pss + SwapPss. PASS iff every C1 cycle's post-drain retained ≤ 1.10 × idle retained, and the three values are not strictly increasing with a total rise > 2 % of idle. G5 never converts a G4 FAIL into a PASS.
- **Soak thermal**: medians of the last three 20 s CPU-temperature windows within 2 °C.

## Verdict per mode

- **GO (isolated qualification)**: G1, G2, G3, G4 PASS (mode 4 also soak). Daily deployment and PR merge remain separate user decisions.
- **HOLD**: G1 and G2 PASS, but G3 or G4 FAIL. If G4 FAILs while G5 PASSes the verdict reads `HOLD (pending adoption of G5)`.
- **NO-GO**: G1 or G2 FAIL.

Regression suite on PRoot and on Termux native for the same SHA, and GitHub governance CI, are reported separately; CI green is not device qualification.
