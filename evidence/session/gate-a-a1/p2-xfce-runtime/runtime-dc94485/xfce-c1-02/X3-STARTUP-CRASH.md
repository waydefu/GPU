# xfce-c1-02 — X3 startup crash (NOT an XFCE run; not consumed)

X3 pid 23886 (`termux-x11gpu com.waydefu.x11gpu :3 -noreset`, commit dc94485) died with
SIGSEGV 1.6 s after launch, before any X client connected and before any XFCE process
existed. The runner saw it only indirectly (`xdpyinfo: unable to open display ":3"`,
terminate `ECONNREFUSED`) and stopped as `XFCE_BLOCKED x_root_size` with an empty size -
a misleading label, fixed in the runner afterwards (exit 4 = X3_STARTUP_CRASH, checked
before the root-size read, launcher-log segment saved per run).

## Signature — matches mem:global/art-jit-crash-triage exactly

```
Uctx signo=11 si_code=1 si_addr=0x0  PC=0x000000004800229c  LR=0x000000712472b8e0
x0=0x61  x1=0x0680f3f8                      (Dalvik heap object space)
Uraw 62/63 = 0x6e6f4d656c646e75 0x62757453726f7469   -> "undleMonitorStub"
native backtrace: xorg_backtrace <- signal handler only
```

PC 0x4800xxxx is the `dalvik-jit-code-cache` mapping of app_process64; the fault is in an
ART runtime stub during early CmdEntryPoint initialisation, not in libXlorie C/C++ code.
Classification (unchanged from the memory): `OBSERVED / VM-JIT-CLASS / ROOT CAUSE NOT
PROVEN`. The same class reproduced historically under PROTO=0, where Gate A is inert.

Segment of the shared launcher log: `x3-launcher.log` (lines 95683-95710 of
p2-runtime-phase1/r0/x3-launcher.raw.log, the only crash dump in that file).

## What it means for V1

Not a Gate A defect, so it does not enter the Gate A gap inventory. It IS a daily-driver
reliability fact: Gate W counts any crash. Tracked as risk R-31 (X startup VM-JIT crash),
with its frequency measured from the launcher log (X starts that reached screen init vs
startup crash dumps) and from every run from now on.

Per the triage protocol: fail-closed for this run (nothing after the crash was
attempted), then ONE bounded rerun of the same variant.
