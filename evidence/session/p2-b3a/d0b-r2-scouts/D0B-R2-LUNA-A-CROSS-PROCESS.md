# D0b-R2 Luna Scout A — Cross-process Contract Inventory

```text
session: 20260912_134201_778f75
model: gpt-5.6-luna-900k
provider: openai-codex
reasoning: max
source: qualification/d0a-narrow-20260912 @ a6cc7952861b8a63740d42bf78553573cfa0eec0
source status: tracked clean
R1: read-only rejected evidence
```

## CONCLUSION

An explicit D0b renderer mode is unnecessary for the narrow Composite class if
renderer region upload is selected universally by the existing
`LORIE_GPU_OP_COMPOSITE`. Producer-only full-versus-partial staging is
conditionally feasible. Existing entry/descriptor/cache data are sufficient for
upload mechanics but do not prove byte freshness or safe reuse. If a distinct mode
bit were required, no existing channel has suitable semantics without changing its
meaning.

## EXISTING CHANNELS

| Channel | Existing data | Usable without ABI change |
|---|---|---|
| GPU copy `op` | COPY/SOLID/COMPOSITE | YES for universal Composite region path; NO as a distinct D0b bit |
| `LorieGpuCopyEntry` | serial, IDs, offsets, rects, op | NO distinct mode needed/carried |
| Shared state | queue indices, completedSerial, surface/root/cursor/telemetry | NO distinct mode field |
| Buffer registration socket | add/remove plus descriptor and FD/AHB handle | NO content mode |
| Buffer descriptor | dimensions, stride, format, type, id | Upload mechanics only |
| Shared-state/GPU-done events | state FD and completion notification | NO mode |
| B3a telemetry | optional observation | NO render-control semantics |

## UNIVERSAL RENDERER PATH

`YES` as static feasibility for valid in-bounds R3 Composite entries:

- D0a off one-shot FD and D0a on cached FD both contain a full current source clone; uploading only the queued sampled rect is semantically sufficient.
- A proposed D0b FD is conditional on copy-before-publish and completedSerial reuse proof.
- A new FD texture has stride-wide NULL storage; initializing only the region sampled by the current nearest draw is sufficient for that draw.
- Cached stale texels outside the current sampled region are irrelevant if every future draw uploads its own exact sampled region first.
- Existing `op==COMPOSITE`, rects, descriptor, and texture lookup carry mechanics; they do not carry freshness proof.

## MINIMUM EVIDENCE

- `lorie.h:171-213`: entry fields and separate-process shared queue.
- `InitOutput.c:2077-2121`: narrow R3 picture predicate.
- `InitOutput.c:1422-1578,2145-2207`: one-shot/D0a full source clone.
- `InitOutput.c:2270-2312,1581-1694`: source rect/op publication.
- `renderer.cpp:745-767,781-918,1352-1374`: texture lookup, upload, same-rect UV draw, forced nearest.
- `buffer.c:635-673`: stride-wide FD texture and full upload.
- `buffer.h:12-27`, `cmdentrypoint.cpp:460-492`, `activity.cpp:193-226`: descriptor/socket framing.

## UNKNOWN / SOL FLAGS

No clean-HEAD D0b producer exists. No source proof makes post-publication
upload/lookup failure unreachable, and no existing failure ack/cancel exists.
Descriptor/ID equality is not content-validity proof. Preserve completedSerial,
ownership, and fence semantics.
