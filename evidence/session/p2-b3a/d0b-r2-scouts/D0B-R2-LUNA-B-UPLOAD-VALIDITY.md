# D0b-R2 Luna Scout B — Upload Failure / Texture Validity

```text
session: 20260912_134209_2cbe9a
model: gpt-5.6-luna-900k
provider: openai-codex
reasoning: max
source: qualification/d0a-narrow-20260912 @ a6cc7952861b8a63740d42bf78553573cfa0eec0
source status: tracked clean
R1: read-only rejected evidence
```

## FAILURE TABLE

| Failure | Class | Prepublish preventable | Texture R valid | Candidate fallback |
|---|---|---:|---:|---|
| null entry / invalid rect count | deterministic | YES | NO | producer fallback |
| invalid FD descriptor/dimensions/stride | deterministic | YES | NO | producer fallback |
| NULL/MAP_FAILED renderer mapping | lifecycle/resource | NO producer proof | NO | no existing postpublish fallback |
| GL texture id 0 | lifecycle/resource | NO producer proof | NO | no existing postpublish fallback |
| arithmetic/rect/row-span overflow | deterministic | YES with mirrored admission | NO | producer fallback |
| GL/API error | runtime | NO | NOT PROVEN | no current result channel |

All R1 deterministic checks occur before its GL upload loop. GL upload calls are
void; R1 converts no GL error into failure. Thus GL error can leave region validity
unproven while the helper reports success.

## FULL-UPLOAD FALLBACK

`NOT PROVEN` universally. For a valid entry, full upload from partially refreshed
staging includes current bytes for sampled R, and stale outside R alone does not
invalidate the narrow current draw. But the existing full upload is void and has no
success result; it cannot recover missing mapping/texture or malformed geometry,
and may encounter the same GL failure.

## SKIP-DRAW

`INCORRECT` with the existing X contract. Skipping and withholding completion does
not replay/fallback the already-published Composite. X only times out/liveness
checks; there is no renderer failure result. Advancing completion would instead
falsely complete a missing/stale draw.

## PREPUBLISH TOTALITY

`NOT PROVEN`. Producer can mirror deterministic geometry/stride/arithmetic checks,
but cannot prove renderer mapping/texture attachment survival or eliminate GL
runtime errors. Existing queue has no upload-failure status.

## MINIMUM EVIDENCE

- Clean `buffer.c:635-674`: NULL-backed FD texture storage and void full upload.
- R1 `renderer.cpp:780-853`: precondition returns and row uploads without GL result.
- R1 `renderer.cpp:947-1015`: failed upload still draws and advances readIndex.
- Clean `renderer.cpp:1102-1153`: fence then completedSerial publication.
- Clean `InitOutput.c:1581-1701`: producer validation/publication.
- R1 `InitOutput.c:2587-2627,2719-2794`: prepublish copy and no consumer-failure fallback.
- Clean `lorie.h:193-213`: no failure/status field.

## UNKNOWN / SOL FLAGS

No runtime/build work was authorized. Driver failure behavior remains unobserved.
Outside-region staleness is harmless only under exact same-region nearest sampling
and per-draw refresh. Existing missing src/dst paths already log and advance the
queue; this is a separate fail-open lifecycle concern.
