# Luna B — Transaction Publication

```text
session: 20260912_033724_9188ba
model: gpt-5.6-luna-900k
provider: openai-codex
reasoning: max
```

## CONCLUSION

Not every current Composite callback publishes: only a successfully scheduled
callback publishes an entry. The transaction-close boundary is DoneComposite.
Existing shared entry fields can describe a delayed per-transaction entry without
new ABI fields, but current private state does not retain every callback source
rectangle.

## CURRENT SEQUENCE

Prepare clears transaction state, validates, clones source, and retains common
src/dst. EXA calls Composite per region box, then Done once. Each Composite
currently constructs one source box and immediately schedules it. The scheduler
assigns serial, fills metadata, barriers, advances writeIndex, and signals renderer.
Renderer drains entries and publishes completedSerial only after fence. Done waits
lastSerial, releases refs, repairs X bytes, and resets state.

## EVIDENCE

- `exa_render.c:749-775`: Prepare, Composite per region box, then one DoneComposite.
- `InitOutput.c:2270-2312`: each callback immediately attempts schedule; failures retry/fallback.
- `InitOutput.c:1581-1701`: success assigns serial and metadata, barriers, then advances writeIndex.
- `lorie.h:180-213`: entry already carries serial, IDs, offsets, numRects, op, telemetry and 16 rects; queue capacity 8.
- `InitOutput.c:2347-2388`, `:1723-1735`: Done is close/release/reset; wait may return false.
- `renderer.cpp:781-918`, `:961-965`: readIndex consumption and post-fence completedSerial publication.

## POTENTIAL ABI IMPACT

`POSSIBLE` — no new shared field is indicated, but delayed publication changes
queue timing/capacity behavior and needs Sol adjudication.

## UNKNOWN

Arbitrary multi-box aggregation beyond 16 rects is not proven. Current private
state has no per-callback source-region list.

## ARCHITECTURE RISK FLAG

`SOL REVIEW`
