# Luna A — Sampling / Bounds

```text
session: 20260912_032500_dfa6f4
model: gpt-5.6-luna-900k
provider: openai-codex
reasoning: max
```

## CONCLUSION

Branch/HEAD/tracked status matched `qualification/d0a-narrow-20260912` at
`a6cc7952861b8a63740d42bf78553573cfa0eec0`.

No source-level proof exists that every currently accepted rectangle satisfies
`0 <= x1 < x2 <= source_width` and `0 <= y1 < y2 <= source_height`. The named
predicates omit bounds. Zero extents are fail-closed, but positive rectangles may
still be negative or overflow right/bottom.

## EVIDENCE

- `exaTryDriverComposite`, `exa_render.c:670-695`: adds drawable origins, computes the destination-clipped region, and applies destination pixmap delta.
- `exaTryDriverComposite`, `exa_render.c:726-772`: folds source/destination pixmap offsets into source coordinates and calls Composite once per region box.
- `miClipPictureSrc`, `mipict.c:264-283`: applies optional client clip; no source drawable width/height bound.
- `lorieCanAccelCompositePictures`, `InitOutput.c:2077-2098`: format/mask/transform/repeat/filter/componentAlpha/alphaMap checks; no geometry bounds.
- `lorieCanAccelComposite`, `InitOutput.c:2101-2121`: pixmap/runtime/sampleability checks; still no rectangle bounds.
- `lorieExaComposite`, `InitOutput.c:2278-2289`: rejects non-positive extent; source dimensions are available here before BoxRec construction.
- `lorieExaComposite`, `InitOutput.c:2303-2310`: schedules the constructed source region without a visible bounds predicate.

## MINIMAL CHECK LOCATION

`lorieExaComposite`, after the non-positive extent guard and before BoxRec casts,
RegionInit, or scheduling. This point has post-offset source coordinates and the
source pixmap dimensions.

## UNKNOWN

The bounded trace did not claim an independent bounds guard inside the scheduler.
No device/build/benchmark was run.

## ARCHITECTURE RISK FLAG

`SOL REVIEW`
