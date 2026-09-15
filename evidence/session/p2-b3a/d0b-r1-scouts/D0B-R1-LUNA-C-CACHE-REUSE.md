# Luna C — Conservative Cache Reuse

```text
session: 20260912_033732_998447
model: gpt-5.6-luna-900k
provider: openai-codex
reasoning: max
```

## CONCLUSION

Current D0a is not fail-closed for cache reuse: false `lorieGpuCopyWait` does not
authorize reuse, but DoneComposite continues cleanup and a later Prepare can hit
and overwrite `d0aStagingCache`. Successful `completedSerial >= lastSerial` is the
only existing completion proof found. There is no producer-visible
renderer-consumed ack.

## FAILURE PATH

- `lorieGpuCopyWait` returns false on connection loss, renderer/surface unavailable, or timeout.
- Renderer fence create/wait failures leave completedSerial unpublished.
- DoneComposite logs failed wait but releases pending/caller refs and resets state.
- Cache-owned ref remains; a later descriptor match can overwrite the same FD without checking completedSerial.
- Descriptor mismatch can unregister/release the old cache after new allocation without an independent completion check.
- Composite retry/fallback sites also ignore wait result.

## EVIDENCE

- `InitOutput.c:1723-1735`: false-wait conditions.
- `InitOutput.c:2353-2388`: cleanup continues after false wait.
- `InitOutput.c:1438-1505`: descriptor-only match and unconditional full-row overwrite.
- `InitOutput.c:1472-1484`: replacement unregister/release.
- `renderer.cpp:738-742,931-965,1115-1153`: completedSerial publishes only after successful fence completion.

## POSSIBLE FAIL-CLOSED OPTIONS

- Refuse reuse and quarantine old cache until an existing completedSerial proof.
- Use fresh one-shot staging while retaining old cache/registration.
- Use software fallback when renderer unavailable; fallback alone does not prove completion.
- Pre-GPU-completion reuse would require a consumed token or equivalent ownership semantics.

## NEW SYNC APPEARS NECESSARY

`POSSIBLE` — not for conservative completedSerial-only reuse; yes for a
pre-GPU-completion consumed boundary.

## UNKNOWN

Late completion/discard behavior after failed wait was not runtime-tested. Exact
renderer-side unregister ownership ordering was not proven.

## ARCHITECTURE RISK FLAG

`SOL REVIEW`
