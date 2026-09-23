# probe-03 — ran with the screen OFF (device Dozing, keyguard showing)

Valid for: the untraced launch path (X3 PPid 8415 = com.termux, TracerPid 0, no
"Tracer detected"), the idle round trip (p50 0.37 ms), and the clean close.
Invalid for everything that needs a visible Activity: the surface was 1200x2464, the X
root 1200x2239, the renderer drew 0 frames, and the R10 workload's 8 composites never
reached the probe (xrender_ops 0, Gate A counters 0). Found after the fact
(`dumpsys power` -> mWakefulness=Dozing). The V3 runner checks the screen before and
after every run.
