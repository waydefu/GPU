# Gate A P2 R6 Present retirement — independent review + patch normalize

Date: 2026-09-16

```text
STATUS: SOURCE REVIEWED / PATCH NORMALIZED / LOCAL COMMIT
R6: NOT PASS / NOT CLOSED / NOT YET VERIFIED
WORKTREE: src/f8-ahb-gatea-r6-retire
BRANCH: fix/gatea-r6-present-retirement-20260915
BASE: 95e6f9602b0146ee190870f84a34aad822ef666f
COMMIT: 0f1e54699d0b11a781f2c044fbc77505f8a53bd8
CI / INSTALL / DEVICE: NOT DONE THIS PACKET
R7: NOT STARTED
```

This is an independent review of the untrusted writer-lane C, plus the
minimum patch-representation correction. It does not rewrite historical
`runtime-95e6f96/` or `runtime-9369553/` cells. It does not claim R6 PASS.

## PRE-EDIT VERDICT

READY for patch normalization only. Present ownership C was already the
retirement helper on disk; the tracked defect was duplicated Present hunks
in `xserver.patch`.

| Item | Live |
|---|---|
| Worktree | `/root/projects/GPU加速/src/f8-ahb-gatea-r6-retire` |
| Branch | `fix/gatea-r6-present-retirement-20260915` |
| HEAD at review | `95e6f9602b0146ee190870f84a34aad822ef666f` |
| Dirty tracked | `lorie/src/main/cpp/patches/xserver.patch` only |
| xserver submodule | `65d790bd208ec380b196eb98f144abb0b32e334d` + expected patch-applied dirty tree |
| Installed APK | still `95e6f96` (not this commit) |

## Ownership reconstruction

Schedule success sets `gpu_copy_pending=TRUE` immediately, before requeue.

| Path | Behavior |
|---|---|
| A pending + incomplete + healthy + requeue OK | remain pending; no ACK |
| B pending + incomplete + natural requeue fail | event 33 → helper wait-or-fatal → event 34 → idle |
| C pending + renderer unavailable | helper; wrapper fail-stops if not done; no scrap |
| D pending + already completed | helper ACK without wait (serial 0 still fatals) |
| E first schedule then requeue fail | pending already true; retire after completion; no early ACK |

`gpu_copy_dst_buffer == NULL` is passed through as legal root destination.

## ACK call sites (Present)

Exactly one executable `lorieGpuCopyAck(` under `xserver/present/`:
`present_vblank.c` `present_gpu_copy_retire_or_fatal`.

EXA `InitOutput.c` ACK sites remain the Done-path (not Present).

`gpu_copy_pending = FALSE` exists only inside the helper.

Event 32 remains defined and uncalled from Present. Runtime use is still
forbidden.

## Scrap / destroy / timeout / CloseScreen

- `present_vblank_scrap`: helper before idle/pixmap destroy.
- `present_vblank_destroy`: helper before pixmap drop.
- Timeout / renderer loss: `lorieGpuCopyWaitForPresentOrFatal` →
  `gateAXFatal` noreturn (`x-present-copy-wait`).
- CloseScreen: DIX `FreeAllResources` destroys windows (helper) before
  `lorieCloseScreen` → `gateACloseGeneration`. SOURCE-PROVEN only.

## Judge

Quiescent-admit requiring a later Composite + second lifecycle is a
**PRODUCT INVARIANT** of DESIGN §6.2 / §9, not a host overfit. Kept.
Not weakened.

## xserver.patch

Removed the appended second Present file trio. Primary
`present_execute.c` / `present_priv.h` / `present_vblank.c` hunks now
apply 65d790b → retirement C in one pass.

Round-trip: forward apply to clean 65d790b matches live dirty Present
files; reverse restores BASE; `git diff --check` PASS.

## Host verification (this session)

```text
verify_r6_design_impl.py                 PASS (incl. present-*-once)
test-present-gpu-copy-retirement.py      PRESENT_RETIREMENT=PASS
test-judge-r6-design.py                  37/37 OK
test-r6-design-bind.sh                   BIND_NEG=PASS
bash -n run/bind scripts                 exit 0
p_r6_d1_queued.c / p_r6_d2_present.c     -Wall -Wextra -Werror exit 0
git diff --check                         exit 0
ninja Xlorie arm64-v8a present rebuild   exit 0, 0 warnings on those files
Gradle full-clean                        NOT RE-RUN (wrapper unicode path)
```

## Not proven

Device D1 / D2-INFLIGHT / D2-OOM on this commit. Timeout/loss/scrap/destroy
runtime. Production Gate A. R7.
