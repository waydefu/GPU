# GATE P2-A.4a — hook topology after install-once probe

> 歷史 gate 證據。本文的 PID、APK 與觀測窗口只描述 A.4a；P2-A 已關閉，目前 runtime 以 `HANDOFF.md` 為準。

```
P2-A.4a: PASS
Topology:
D0 depth max = 1
D3 = 1
probe recursion = 0
probe_enter_count = 1
probe_return_count = 1
max_probe_depth = 1
current / saved / callee do NOT form a cycle
1×1 Composite: SURVIVED
X :3 still alive (PID 32075 ppid=1)
Implication:
P2 crash root cause was instrumentation hook corruption, not backing/pitch.
Next gate: A.4b
```

A.3 remains **ROOT CAUSE CONFIRMED** (`damageComposite ↔ lorieCompositeProbe` from a second `lorieInstallXRenderProbe`). This gate only checks that commit `6182b94` broke that cycle.

---

## Safety

- Stable `:1` PID **26474** `termux-x11 com.termux.x11 :1 -legacy-drawing` — alive before install, after `:3` up, after 1×1 PASS.
- Experimental only: `com.waydefu.x11gpu` `1.03.01-6182b94-07.09.26`.
- No xfwm / XFCE. No P0/P1 reopen. No `sys_ptr` / pitch / Damage-bypass / `if (depth > N) return`.

---

## Build

| | |
|---|---|
| commit | `6182b94bc69166e49a2f6ca0238ffdba9781fc68` `f8-p2-a4-diag` |
| CI | GitHub `waydefu/termux-x11` run **34157648272** success |
| APK | `com.waydefu.x11gpu` `1.03.01-6182b94-07.09.26` |
| SHA256 | `9f2f8651378c3bbd3cbccff0566538d64af7cf22e349c874c470d848935cd42b` |
| install | session `1011927578` `pm install-create/write/commit` → **Success** |
| stable pkg | still `com.termux.x11` `1.03.01-11b82d9-06.09.26` |

---

## Install sequence stamps

Five `InstallProbe installed=0` lines, all with the same underlying pointer. **No SKIP** (expected: `lorieCloseScreen` clears `xrenderProbeInstalled` on RandR / screen rebuild; the removed `CreateScreenResources` second site did not fire).

```
InstallProbe installed=0 saved=0x7498d416e0 new=lorieCompositeProbe current=0x7498d416e0
```

`saved` is **exaComposite** (`0x31e6e0`), never `damageComposite`. Re-install after CloseScreen does **not** recreate the A.3 cycle.

---

## 1×1 Composite topology (one flight)

```
D0  damageComposite ENTER depth=1
    current=0x7498ca2e58   damageComposite
    saved  =0x7498b0f35c   lorieCompositeProbe
D1  BEFORE_UNWRAP
D2  AFTER_UNWRAP/BEFORE_CALL depth=1
    callee=0x7498b0f35c    lorieCompositeProbe   (not a self-cycle)
Probe ENTER depth=1 max=1 enter=1 return=0
    saved=0x7498d416e0     exaComposite   (NOT damageComposite)
E0  EXA_COMPOSITE_ENTER  1×1
E0u EXA_UNACCEL_ENTER
E1  PRE_FB_COMPOSITE callee=0x7498c20934  fbComposite
Sfb role=src / dst  1×1 bpp=32
Probe RETURN depth=1 enter=1 return=1
D3  AFTER_CALL depth=1
```

Tester: `RESULT render-last PASS mode=1x1 X alive` (`tester_rc=0`). `:3` PID **32075** still up; `xdpyinfo :3` ok.

---

## Stamp table

| Stamp | Count | Meaning |
|---|---|---|
| InstallProbe installed=0 | 5 | ScreenInit after CloseScreen/RandR; same saved=exaComposite |
| InstallProbe SKIP | **0** | flag cleared on CloseScreen; 2nd CreateScreenResources site gone |
| D0 / D1 / D2 | **1** | depth **1** only (A.3 was 1029) |
| D3 | **1** | inner Composite returned (A.3 was 0) |
| Probe ENTER / RETURN | **1 / 1** | max_depth=1 |
| E0 / E0u | 1 / 1 | noted for A.4c; not required for A.4a |
| E1 | 2 | PRE_SWAP + PRE_FB |
| Sfb | 2 | src+dst 1×1; **survived** — do not start a new backing/pitch campaign |
| Ssig / Uctx | **0** | no SIGILL / no crash handler |

---

## Pointer identity (exact APK/ELF)

`libXlorie.so` r-xp base `0x7498a23000` (`/proc/32075/maps`). Unstripped CI `34157648272`:

```
0x7498ca2e58  +0x27fe58  damageComposite     damage.c:491
0x7498b0f35c  +0xec35c   lorieCompositeProbe InitOutput.c:809
0x7498d416e0  +0x31e6e0  exaComposite        exa_render.c:878
0x7498c20934  +0x1fd934  fbComposite         fbpict.c:50
```

Chain for this 1×1:

```
damageComposite
  unwrap → lorieCompositeProbe
    saved → exaComposite
      ExaCheckComposite / unaccel
        fbComposite
          Sfb → RETURN → D3
```

`current == saved == callee` after unwrap is the **normal** Damage unwrap (callee is the probe). It is not A.3’s cycle: probe `saved` is `exaComposite`, depth stays 1, D3 fires.

---

## Verdict

**PASS.** Topology criteria all met. 1×1 Over onto a pixmap completed and the experimental server stayed up.

**P2 crash root cause was instrumentation hook corruption, not backing/pitch.**

E0/E1/Sfb fired on this surviving 1×1; record for **A.4c**, do not reopen pixmap/EXA/fb/pixman diagnosis here.

Next gate: **A.4b** (probe enter/return already 1=1 and max_depth=1 on this flight; A.4b can extend coverage). Do not start XFCE until that topology work is accepted.
