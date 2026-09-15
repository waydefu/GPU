# GATE P2-A.3 — Composite hook-chain / pre-fb boundary

> 歷史 gate 證據。本文記錄 A.3 對 probe hook cycle 的裁決；PID、APK 與當時測試環境不代表目前 runtime，現況以 `HANDOFF.md` 為準。

```
P2-A.3: ROOT CAUSE CONFIRMED
Failure:
Composite hook cycle / infinite recursion.
Cycle:
damageComposite
→ lorieCompositeProbe
→ damageComposite
→ ...
Cause:
lorieInstallXRenderProbe is invoked twice.
Second installation occurs after DamageRegister and overwrites
lorieSavedComposite with damageComposite while Damage's saved
Composite already points at lorieCompositeProbe.
Evidence:
D0/D1/D2 = 1029
depth = 1 → 1029
D3 = 0
E0/E0u/E1/Sfb = 0
current == saved == callee
= 0x6dd9910028
llvm-addr2line:
0x6dd9910028
→ lorieCompositeProbe
→ InitOutput.c:803
Terminal failure:
SIGILL after stack exhaustion.
EXA/fb/pixman:
NOT REACHED.
Repair gate:
OPEN — histogram probe wrapper lifecycle only.
```

**Question:** After MASK `PrepareAccess` succeeds, where does control die before `create_bits_picture()`?

**Answer:** In `damageComposite`’s unwrap/call. The “lower” Composite pointer is `lorieCompositeProbe`, which calls back into `damageComposite`. This is not an unknown EXA/fb pitch bug.

P2-A.2 remains `INCONCLUSIVE / A eliminated`. This gate closes the pre-fb interval.

---

## Safety

- Stable `:1` PID **26474** `termux-x11 com.termux.x11 :1 -legacy-drawing` — alive throughout.
- Experimental only: `com.waydefu.x11gpu` `1.03.01-7482b83-07.09.26`.
- Observe-only stamps. No behavior change to sys_ptr / TrueNoop / PrepareAccess / GPU Composite.
- One `p-render-last 1x1`. `:3` died. `:1` still up.

---

## Stamp table (this 1×1)

| Stamp | Count | Meaning |
|---|---|---|
| Sprep | 2 | 16×16 bpp=1 MASK `index=2` only, before the cycle |
| D0 | **1029** | `damageComposite` ENTER, depth 1…1029 |
| D1 | 1029 | BEFORE_UNWRAP |
| D2 | 1029 | AFTER_UNWRAP / BEFORE_CALL |
| D3 | **0** | never returned from the inner call |
| E0 | **0** | `exaComposite` never entered |
| E0u | **0** | `ExaCheckComposite` never entered |
| E1 | **0** | no pre-fb Composite |
| Sfb | **0** | `create_bits_picture` never reached |
| Uctx | **0** | SIGSEGV handler not invoked |
| Ssig | 1 | `Caught signal 4` (SIGILL) via OsSigHandler |

Every D0/D1/D2 line (depth 1 included):

```
op=1 (PictOpSrc)
pMask=0
current=0x6dd9910028
saved=0x6dd9910028
callee=0x6dd9910028
saved_is_self=0
callee_is_self=0
```

`callee_is_self` compared against `damageComposite`. It is **false** because the pointer is not `damageComposite`; it is the histogram probe (below). The self-cycle is still proven by depth and by D3=0.

First / last:

```
D0 depth=1    … current=saved=callee=0x6dd9910028
D2 depth=1    callee=0x6dd9910028
D0 depth=2    (same pictures, same pointers)
…
D0 depth=1029
Ssig Caught signal 4 si_code=2 si_addr=0x6dd9b490d8
```

---

## Decision tree result

```
MASK PrepareAccess(index=2) succeeds   (2 Sprep lines)
│
├─ D0 depth 1,2,3,…,1029
│    D2 callee = lorieCompositeProbe
│    D2 callee == current == saved
│    D3 never
│         → HOOK RECURSION CONFIRMED
│
├─ E0 / E0u / E1 / Sfb absent
│         → damage wrapper NOT cleared; EXA/fb never next
│
└─ ucontext PC: not captured (died as SIGILL, handler was SEGV/BUS only)
     OsSigHandler “Caught signal 4” + libunwind frames are secondary.
```

---

## Symbolication (exact APK/ELF)

`0x6dd9910028` → file offset `0xec028` → **`lorieCompositeProbe`**
`lorie/src/main/cpp/lorie/InitOutput.c:803`

```
nm libXlorie.so
  00000000000ec028 t lorieCompositeProbe
  000000000027fa04 t damageComposite
  000000000031e28c t exaComposite
  00000000001fd4e0 T fbComposite
```

`lorieCompositeProbe`:

```c
xrenderHistRecord(...);
if (lorieSavedComposite)
    lorieSavedComposite(...);   /* no unwrap of PictureScreen */
```

`lorieInstallXRenderProbe` is called **twice**:

1. `lorieScreenInit` after `exaDriverInit` (`InitOutput.c:1069`)
2. `lorieCreateScreenResources` after `DamageRegister` (`InitOutput.c:875`)

The second call’s guard is `ps->Composite == lorieCompositeProbe`. After Damage wraps, `ps->Composite` is `damageComposite`, so the guard misses. Second install sets:

```
lorieSavedComposite = damageComposite
ps->Composite       = lorieCompositeProbe
```

while Damage’s saved lower is already `lorieCompositeProbe`.

Cycle:

```
damageComposite
  unwrap: ps->Composite = saved = lorieCompositeProbe   (no-op if already equal)
  call ps->Composite
    → lorieCompositeProbe
         → lorieSavedComposite
              → damageComposite
                   → …
```

That matches every D0/D1/D2 line: `current == saved == callee == lorieCompositeProbe`.

---

## What this is not

- Not Scudo Primary guard.
- Not `sys_ptr` / `fb_ptr` pitch mismatch as the **first** bad layer (fb never runs).
- Not confirmed pixman. Sfb never fires.
- `callee_is_self=0` is not a counter-proof; the compare used `damageComposite`, not the probe.
- `_Unwind_Backtrace` repetition from P2-A.2 is now explained: real recursion, not unwind fiction.

## Open consistency note (does not undo the cycle)

P2 composite-matrix **Dst 3/3 PASS** is still unexplained if every Composite hits this cycle. Possible: wrap only poisons after a non-Dst fallback / second install ordering; Dst may not be a counterexample to this 1×1 Over/Src flight. Do not use Dst-alive to reopen AHB as #1.

---

## Repair (eligible; not done in this gate)

Observation-only constraint still held for the binary that produced this snap.

Eligible fix (do **not** implement a `if (depth > N) return` bailout):

1. Install the histogram probe **once**, after Damage is up, **or** skip the second `lorieInstallXRenderProbe` if `lorieSavedComposite` is already set.
2. Prefer not occupying `ps->Composite` with a wrapper that Damage unwrap will stomp or re-enter. `ProcRenderComposite` / a cooperating wrap is safer.
3. Re-run `p-render-last 1x1` on `:3`. Expect D0 depth=1, D2 callee=`exaComposite` or `ExaCheckComposite`/`fbComposite`, then E0/E1/Sfb — or a surviving Composite.

Until that repro, do not change `sys_ptr` / `PixmapIsOffscreen`.

---

## P2-A.2 (unchanged)

```
P2-A.2: INCONCLUSIVE
A: ELIMINATED
B: NOT SUPPORTED
C: NOT SUPPORTED
D: NOT ESTABLISHED
```
