# R9 DESIGN FREEZE — Q7 / Q8 RESOLVED (partial)

DATE 2026-09-21  MODE host-only probe, read-only, no device mutation, no attempt consumed
SCOPE Answers only Q7 and Q8 of the eleven §8.2 questions. Q1–Q6 and Q9–Q11 remain OPEN.

## Q8 — can process starttime be obtained stably? **YES**
```
source    /proc/<pid>/stat field 22 (starttime), units of 1/SC_CLK_TCK
SC_CLK_TCK = 100   -> starttime is in centiseconds since boot
coverage  71 of 71 live PIDs returned a value; 0 failures
stability same PID read 1.2 s apart returned the identical value
          (Stable :1, PID 15071, starttime 1621498 both times)
parsing   comm may contain spaces and parentheses, so field 22 must be taken
          relative to the LAST ')' in the line, never by naive whitespace split
```
`/proc` is fully readable for this field under Ubuntu PRoot on this device. This is
**not** one of the PRoot-restricted interfaces (unlike `/proc/net/tcp`, which is
EACCES here — see V-7R).

## Q7 — is PID alone sufficient for process identity? **NO**
PID reuse is a live risk on Android: the kernel recycles PIDs, and an R9 generation
boundary is exactly the moment where one process exits and another starts. Two
observations taken either side of that boundary can collide on PID while referring to
different processes.

`/proc/sys/kernel/pid_max` is **not readable from inside this PRoot**, so the exact
wrap distance cannot be quoted here; 73 live processes were observed. The absence of a
readable bound is itself a reason not to rely on PID: the safety margin cannot be
computed.

## Ruling (§8.3 satisfied — no DESIGN_REQUIRED escalation needed)
```
process identity = (PID, starttime)      ADOPTED — both components available
process identity = PID                   FORBIDDEN
```
§8.3's fallback clause ("starttime 不可得 → DESIGN_REQUIRED (D-13)") does **not**
trigger: starttime is available and stable, so D-13 is not raised.

Every R9 packet that compares a process across a generation boundary must carry the
tuple, and must record both components in evidence so the comparison is auditable
after the fact.

## Still OPEN — R9 cannot be designed on this alone
```
Q1  warm new X with same Activity: what does the Activity retain?
Q2  cold Activity restart: what is genuinely rebuilt?
Q3  generation nonce lifecycle: allocated when, invalidated when, compared by whom
Q4  renderer retained state across generations
Q5  stale READY visible to a new generation        <-- §8.2 calls this the most
                                                       dangerous UAF surface
Q6  stale generation frames entering a new generation
Q9  socket lifecycle and cross-generation residue
Q10 same-process reset support (decides whether R9-RESET exists at all)
Q11 clean recovery after fatal (F2 acceptance depends on it)
```
Q1–Q6 and Q9–Q11 all require source tracing of comparable depth to
`V2-R8-D-SRC-TRACE`. Until they are resolved, per §8.1 R9 must not be run off PR #7's
design, and no R9 packet may be expanded.
