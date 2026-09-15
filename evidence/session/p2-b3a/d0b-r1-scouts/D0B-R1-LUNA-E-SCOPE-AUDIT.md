# Luna E — Scope Audit

```text
session: 20260912_034944_ee989e
model: gpt-5.6-luna-900k
provider: openai-codex
reasoning: max
```

## SCOPE TABLE

| Area | Appears touched | Evidence |
|---|---|---|
| Queue ABI | NO | Existing write/read ring can be reused (`lorie.h:203-213`, `InitOutput.c:1638-1694`). |
| LorieGpuCopyEntry layout | NO | Existing numRects/rects carries source boxes (`lorie.h:180-191`, `renderer.cpp:781-918`). |
| completedSerial semantics | NO | Candidate only reads existing post-fence proof (`InitOutput.c:1704-1735`, `renderer.cpp:931-967`). |
| New fence | NO | Existing renderer fence is sufficient for conservative reuse. |
| Renderer-consumed ack | NO | Candidate waits later completedSerial boundary. |
| AHB/FD ownership | NO | Existing locked BGRA AHB and FD staging remain. |
| Refcount transfer | NO | Existing cache/caller/per-entry refs can remain. |
| DoneComposite semantics | NO | Existing wait/release contract can remain; private cache guard may fail closed. |
| CloseScreen | NO | No candidate teardown operation. |
| Mutex recovery | NO | Existing queue/fence path only. |
| Generation/epoch | NO | Conservative path needs no new field; ambiguity must fail closed. |
| Shader | NO | Existing UV rectangle draw remains. |
| Blend | NO | Existing Composite blend remains. |
| X-byte repair | NO | Destination repair remains separate. |
| Gate A | NO | FD staging retained. |
| Gate H | NO | No hybrid/lifecycle routing. |

## UNEXPECTED DEPENDENCIES

None among the listed architecture surfaces. Direct candidate touchpoints were
identified as InitOutput cache/geometry logic, the LorieBuffer upload helper, and
renderer use of existing entry rectangles.

## UNKNOWN

No implementation diff existed during the audit. Exact cache serial/quarantine
state, fragmented-box copy timing, and row-upload helper still required review.

## ARCHITECTURE RISK FLAG

`NONE` — evidence only, not authorization.
