# Gate A P2 CASE_LOOP repair-validation cell — designed 2026-09-16, **NOT STARTED**

This is the next-cut contract. It is **not** authorization to install.
It is **not** B-2. It is **not** R7.

## Locked status

```
R6 PASS / frozen 0f1e546
RCA-1 timeout→Done = FIXED / DEVICE-PROVEN (0d72332)
CASE_LOOP consume stall = DEVICE-PROVEN (feeaa56 stall-obs-01)
root mechanism = SOURCE-SUPPORTED (waitForNextFrame + lost wakeup / unbounded idle wait)
hardened candidate = 7549e3667ec03b8b5e50d2e5befe03065840bbd9
CI PASS 35084701124 / artifact QUALIFIED
device still feeaa56
327b028 = initial source fix / SUPERSEDED
B-2 BLOCKED
R7 NOT STARTED
Production Gate A BLOCKED
```

The only CASE_LOOP source SHA worth installing on the phone is **`7549e36`**.
Do not install `327b028`.

Two clocks stay distinct:

- renderer idle recovery: 8 ms CLOCK_MONOTONIC recheck (`LORIE_RENDERER_FRAME_WAIT_NS`)
- EXA completion fail-stop: 2000 ms (`lorieGpuCopyWait(serial, 2000)`)

## Purpose

Prove on device that `7549e36` closes the CASE_LOOP failure mode.
Do **not** mix this with B-2 qualification.

## Cell (when separately authorized)

```
install 7549e36 experimental only (com.waydefu.x11gpu)
→ bind APK SHA256 / Build ID / signer to CI 35084701124
→ fresh :3
→ NO_GATEA_ENV
→ one bounded observation of the same family as feeaa56 stall-obs-01
→ require:
     no >2 s consume stall
     no x-exa-composite-wait fatal
     Composite exact
     Stable :1 untouched
→ STOP
```

PASS of this cell is **not** B-2 PASS.
FAIL of this cell does **not** reopen RCA-1.

After PASS, B-2 requalification from `7549e36` still needs a **new** grant.

## Forbidden until that grant

- install `7549e36` or `327b028`
- retry `runtime-feeaa56/stall-obs-01`
- start B-2 / R7 / R8+
- change 2000 ms
- touch Stable / HDMI
