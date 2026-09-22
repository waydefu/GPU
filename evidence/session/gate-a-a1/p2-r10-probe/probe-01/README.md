# R10 PROBE-01 — what is actually measurable, measured

DATE 2026-09-22  PRODUCT `dc94485` / APK `1bd8bef0…b8a3`
SERIAL `192.168.1.104:36405` (lane 5038; the endpoint changed from the R9 runs —
the phone moved network, so never hardcode it)
X `termux-x11gpu com.waydefu.x11gpu :3 -noreset` pid 6680 · Activity pid 24987
STABLE `com.termux.x11` `:1` untouched throughout.

**This is a PROBE, not an attempt.** It consumes no R10 round, judges nothing, and
its numbers are inputs to `V2-R10-DESIGN`, not results.

## Sequence

```
start X3 -noreset · am start Activity
P0                      sample: bound, no Gate A work yet
w1..w6                  six PictOpOver composites (p_r9_boundary, 64x64 pair)
P1..P6                  a sample after each
clean close             p_r8_lifecycle --cell R8-C1 (test-control terminate)
P7                      sample: X gone, Activity SURVIVING
```

## The clean-close signature — this is the R10 PASS shape

```
GATEA_SUMMARY where=x-close-screen nonce=0 generation=0 generationFatal=0
  c12 AHB_ACQUIRE      16   c13 AHB_RELEASE       16    balanced
  c14 EGLIMAGE_CREATE  16   c15 EGLIMAGE_DESTROY  16    balanced
  c16 TEXTURE_CREATE   16   c17 TEXTURE_DELETE    16    balanced
  c18 X_REGISTRY_CURRENT         0
  c19 RENDERER_REGISTRY_CURRENT  0
  c20 LEASE_CURRENT              0
  c24 GENERATION_FATAL           0
  c25 UNREGISTER  16   c26 RESOURCE_DESTROY 16   c27 GENERATION_CLOSE 1
```

Every allocation balanced, both registries empty, lease zero, no fatal, and the close
zeroed `sessionNonce` and `generation` (Q10). **Nothing here needs a tolerance** —
these are protocol counters, not measurements.

> This also shows why the counter-index fix (`b68770f`) was load-bearing. Reading
> c25/c26 as "registry current", as the tooling did before, would have reported
> **16 and 16** on this perfectly clean close — a fabricated leak in every R10 round.

## Process metrics — what is readable, and how

```
X server      local /proc/<pid>/*            everything, no restriction
Activity      adb shell cat /proc/<pid>/stat|status|statm      OK
              adb shell ls  /proc/<pid>/fd                     Permission denied
              adb shell cat /proc/<pid>/maps                   empty
              adb shell cat /proc/<pid>/smaps_rollup           empty
              adb shell run-as com.waydefu.x11gpu <same>       ALL OK
              adb shell dumpsys meminfo <pkg>                  GPU attribution
```

`run-as` works because the experimental APK is debuggable; it drops to the app's own
uid. **A shell redirect must never be used with it** — `run-as pkg wc -l < /proc/X/maps`
is evaluated by the OUTER shell, which has no permission, and yields an empty string
that looks like a reading. Use `run-as pkg wc -l /proc/X/maps`.

`dumpsys meminfo` is the only source for `EGL mtrack`, `GL mtrack` and `Gfx dev`,
i.e. the only view of GPU-attributed memory. /proc cannot give it.

## Measured noise — the reason the workload has to change

Seven samples across six identical 64x64 composites:

```
metric                       P0     P1     P2     P3     P4     P5     P6
x.fd_count                   88     88     88     88     88     88     88
x.maps_count               3004   3007   3007   3007   3007   3007   3007
x.pss_kb                  78527  78240  78243  78243  78243  78130  78114
activity.fd_count           170    205    207    208    209    210    175
activity.maps_count        4006   4038   4038   4038   4038   4038   4014
activity.pss_kb           63156  63157  62965  62961  62858  62850  62762
activity.egl_mtrack_kb    10408  45312  39536  39536  39536  39536  10424
activity.gfx_dev_kb         928   1044   1052   1060   1064   1072    988
```

**X side is quiet.** `fd_count` is exactly constant, `maps_count` takes one +3 step
on first GPU work and never moves again, PSS drifts down. It is a good detector.

**Activity side is not.** Three things happen at once and only one of them is Gate A:

1. a one-time ramp on first GPU work (`fd` +35, `maps` +32) — driver init, not a leak;
2. a slow monotonic rise (`fd` +1/iteration, `gfx_dev` +8 KB/iteration) that looks
   exactly like a leak for five samples — and is then **fully reclaimed at P6**
   (`fd` 210 -> 175, `maps` 4038 -> 4014, `egl_mtrack` 39536 -> 10424);
3. `egl_mtrack` swinging by ~35 MB between samples, which is the display swapchain,
   not the 32 KB of pixmaps the workload actually allocates.

```
=> A 64x64 pair is ~32 KB. Every Activity-side memory metric has a noise band
   two to three ORDERS OF MAGNITUDE larger than the thing being measured.
   R10's workload must allocate enough Gate A memory to clear that floor, and
   R10 must characterise the idle noise before it judges anything.
```

This is `V2-R10-DESIGN` §4 (workload sizing) and §6 (noise characterisation run).

## Activity residue across one whole session

`P0 -> P7` spans six composites, a clean close, and X's exit, on the surviving
Activity process:

```
fd_count      +1        maps_count    +12       threads     +1
rss_kb        +80       pss_kb     +1393       native_heap +833
gfx_dev      +108       egl_mtrack -10392      (released)
```

Small, and the GPU memory went **down**. Whether the ~1.4 MB PSS is per-session
accumulation or ordinary variance is exactly what R10-B answers over >= 5 sessions —
one sample cannot.

## Activity survival across a clean close — D-06 §2.4, live on this artifact

```
X GONE after the test-control terminate
Activity pid 24987 STILL RUNNING
```

The renderer unbinds at `GENERATION_CLOSE` (`renderer.cpp:846`), so the later socket
HUP classifies `UNBOUND` and does not terminate the process. R10-B is built on this.

## System residue

```
/tmp/.X11-unix/   only X1 (Stable). X3 socket removed.
no leftover x11gpu process
```
