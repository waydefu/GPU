# S3 Gate Ledger

| Gate | Status | Authority evidence | Do-not-reopen note |
|---|---|---|---|
| Phase 0 baseline / Stable isolation | ✅ DONE | `evidence/baseline/` | Stable is production; any damage stops all work |
| P0 non-legacy display | ✅ CLOSED | experimental `:3` gates | historical +768 is lifecycle artifact, not renderer offset |
| P1 LOCAL DRI3/AHB | ✅ CLOSED | experimental `:3` | LOCAL CLOSED ≠ upstream Termux:X11 PR closed (#1095/#1114 still open upstream) |
| GPU Present | ✅ QUALIFIED | `evidence/present/` | — |
| Fence | ✅ QUALIFIED | `evidence/fence/` (+ frametimeline baseline recorded) | 1080p solid: GPU not faster than CPU (recorded, not a failure) |
| EXA Copy (GXcopy distinct AHB) | ✅ PASS | `evidence/exa/copy-gate.txt` (202/202 px, 203/203 offload; overlap = software) | — |
| EXA Solid (GXcopy) | ✅ PASS | `evidence/exa/solid-gate.txt` (matrix + X-byte repair) | — |
| P2-A Composite crash | ✅ CLOSED | `evidence/session/p2-a4/` (A.3/A.4: install-once probe, recursion `damageComposite ↔ lorieCompositeProbe`) | probe recursion / sys_ptr / pitch / PixmapIsOffscreen theories stay closed |
| P2-B.1 workload census | ✅ PASS | `evidence/session/p2-b1/` (1776 Composite, 1166 Over/no-mask candidates) | — |
| P2-B.2 R3 GPU Composite | ✅ PASS | `evidence/session/p2-b2/GATE-P2-B.2.md` (corrected oracle 1514/1514, maxΔ=0; stress + bounded XFCE) | R3 predicate stays narrow; ±1 UNORM never counts as PASS |
| S3 LINK / S3-Q1 / S3-E1b / S3-X1 | ✅ CLOSED | `evidence/session/s3/GATE-S3-RUNTIME.md` (E1b `9b6420d`, run `34396950445`, APK `cd61…7988`) | per-entry proc telemetry NOT EMITTED; follow-up OPTIONAL/DEFERRED |
| S3 runtime (behavioral) | ✅ CLOSED — PASS WITH OBSERVABILITY LIMITATION | `evidence/session/s3/` (launch/XKB/R3/x100/mixed100/lifecycle PASS, Stable untouched) | — |
| Build recovery | ✅ CLOSED | `evidence/session/s3/GATE-S3-RUNTIME.md` (quad/patch-channel/ISA-mismatch blockers) | — |
| P2-B.3a cost census | 🟢 UNBLOCKED 2026-09-10 — telemetry repair (`1954f82`, CI `34407348596`) re-qualified; Tier-1 smoke first, then full paired matrix | `evidence/session/p2-b3a/` (per-session count validation required: mid-session CloseScreen can truncate a tail) | — |

No gate below P2-B.3a has started. XB / Gate A / Gate D / Gate S / Gate H /
Gate W / V1-Core are all future work gated on a clean qualification build.
