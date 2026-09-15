# GATE P2-A.4e — XFCE / original P2 workload qualification

> 歷史 gate 證據。本文的 PID、APK 與觀測窗口只描述 A.4e；P2-A 已關閉，目前 runtime 以 `HANDOFF.md` 為準。

```
P2-A.4e: PASS
XFCE/xfwm stayed up for the observation window (~47s, bounded)
X :3 PID 32075 ppid=1  xdpyinfo ok throughout
probe max_depth = 1  (every ENTER; 0 of 1776 had max>1)
ENTER = 1776  RETURN = 1776  ratio = 1.0
lifetime enter=1881 return=1881  (A.4d 105 + XFCE 1776)
D0 = D3 = 1776  depth max = 1
Ssig/Uctx/Fatal/SIGILL/SIGSEGV = 0
Stable :1 PID 26474 untouched
First XFCE Composite = 5×24 Over (Gate 2 / flight seq-404 shape) — returned
```

A.4a remains **PASS**. A.4b remains **PASS**. A.4c remains **PASS**. A.4d remains **PASS**. A.3 remains **ROOT CAUSE CONFIRMED** (hook cycle). This gate only asks whether **desktop Composite** on experimental `:3` is also stable after the install-once probe repair. Qualification, not a new crash campaign. No `sys_ptr` / pitch / PrepareAccess patch. No commit.

P2-A.4 repair (probe install-once) is sufficient for both the 1×1 crash repro and a bounded XFCE Composite session on :3.

---

## Safety

- Stable `:1` PID **26474** `termux-x11 com.termux.x11 :1 -legacy-drawing` — alive PRE, after XFCE map, every 5s sample, and at write-up (`2026-09-08T04:48:32+08:00`, elapsed ~05:52:23). DISPLAY `:1` was not queried.
- Stable `:1` XFCE left alone: xfce4-session **27590**, xfwm4 **27716**, xfce4-panel **27787**, xfdesktop **27800**. Isolated `:3` session used `HOME=/tmp/xfce-x3-home` and `XDG_*` under `/tmp/xfce-x3-*` so `:1` xfconf was not written.
- Experimental only: `com.waydefu.x11gpu` `1.03.01-6182b94-07.09.26` SHA256 `9f2f8651378c3bbd3cbccff0566538d64af7cf22e349c874c470d848935cd42b` on `:3` PID **32075** ppid=1 (same instance as A.4a–A.4d). Reused; `xdpyinfo :3` ok. Display0 waydefu already resumed; did not restart X, did not `start-activity`.
- No `sys_ptr` / pitch / Damage-bypass / `if (depth > N) return` / SIGILL special-case / force software. Histogram probe left on. No commit / push / CI. P0/P1 not reopened.

---

## Method

Reused live `:3` PID 32075. Isolated XFCE (proven Gate 4 pattern, compositor **on** in xfconf, not `--compositor=off`):

```
unset SESSION_MANAGER DBUS_SESSION_BUS_ADDRESS …
DISPLAY=:3 HOME=/tmp/xfce-x3-home
XDG_CONFIG_HOME=/tmp/xfce-x3-config  (xfwm4.xml use_compositing=true)
dbus-run-session -- xfce4-session
```

Then `xfce4-terminal --display=:3 -T a4e-qual` after map. Observation **45s after map** (~47s total), not an unbounded soak. Logcat `--pid=32075` only (no `-c`). Snap window from `/tmp/x11gpu-p2a3.snap` offset 634797.

---

## PIDs (experimental `:3` XFCE)

| Process | PID | PPID | DISPLAY |
|---|---|---|---|
| dbus-run-session | **11174** | 1 | `:3` |
| xfce4-session | **11177** | 11174 | `:3` |
| xfwm4 | **11216** | 11177 | `:3` |
| xfce4-terminal | **11235** | 1 | `:3` |
| xfsettingsd | **11310** | 11177 | `:3` |
| xfce4-panel | **11371** | 11177 | `:3` |
| xfdesktop | **11419** | 11177 | `:3` |
| X `termux-x11gpu … :3` | **32075** | 1 | — |

`xlsclients :3` after observe: xfce4-session, xfwm4, xfce4-terminal, xfsettingsd, xfce4-panel, Thunar, xfdesktop, notifyd, nm-applet, panel wrappers.

xfconf `/general/use_compositing` = **true**. xfwm logged `Unsupported GL renderer (llvmpipe …)` (GL compositor path not used). `_NET_WM_CM_S0` was not advertised; XRender traffic still included redirected full-screen dest (1200×2191) plus window Over+mask — desktop Composite, not the 1×1 tester.

---

## Probe / Composite window (snap offset 634797 → 9601515)

| | |
|---|---|
| D0 / D1 / D2 / D3 | **1776 / 1776 / 1776 / 1776** |
| Probe ENTER / RETURN | **1776 / 1776** (ratio 1.0) |
| D0 depth max / min | **1 / 1** |
| probe max on every ENTER | **1** (0 with max>1) |
| cycle hints (`saved_is_self` / `callee_is_self`) | **0** |
| lifetime enter / return | **1881 / 1881** |
| Ssig / Uctx / Sbt / Fatal | **0** |
| E0 / E0u / E1 / Sfb | 2030 / 2624 / 5248 / 6014 (nested PrepareAccess lines; not 2× probe) |

One sample at t+16s showed ENTER=1279 RETURN=1278 (one in-flight); they matched on the next sample. Not a cycle.

First XFCE Composite in this window (lifetime enter=106 — the first after A.4d’s 105):

```
D0 depth=1 op=3 saved_is_self=0
Probe ENTER max=1 enter=106 return=105 saved=exaComposite
E0  xywh=0,0,5,24  Over  (Gate 2 last-request shape)
E0u + Sfb src/dst 5×24
Probe RETURN enter=106 return=106
D3 depth=1
```

That 5×24 Over is the original P2 / xfwm compositor-off killer. It **returned**. Later dest is full-screen 1200×2191 (panel/shadow Over+mask, e.g. 851×549 flags=0x11).

Last in window: op=3 306×49 onto 1200×2191 dst, Probe RETURN enter=1881 return=1881.

---

## Histogram (5s dumps during XFCE)

`xrender_ops` 303+450+374+336+313 = **1776** (pairs with D0/ENTER). Not 2× per request.

| t | ops | notes |
|---|---|---|
| 04:46:41 | 303 | startup; 4×29 / 16×16 Over |
| 04:46:46 | 450 | still mapping |
| 04:46:51 | 374 | 15.4 FPS; **1200×2191**; mask Over 851×549 flags=0x11 |
| 04:46:56 | 336 | 21.0 FPS; 1200×2191 Src; 1224×59 / 330×81 mask |
| 04:47:01 | 313 | 16.4 FPS; same compositor-shaped cells |

After ~26s Composite went idle (no new D0 for the remaining ~20s). Session stayed up. Bounded; not a soak.

logcat `--pid=32075`: **no** `Fatal signal` / SIGSEGV / SIGILL.

---

## Live at write-up

| | |
|---|---|
| `:1` | PID **26474** ppid=4718 `termux-x11 com.termux.x11 :1 -legacy-drawing` |
| `:1` XFCE | 27590 / 27716 (untouched) |
| `:3` | PID **32075** ppid=1 `termux-x11gpu com.waydefu.x11gpu :3` (~37 min, same as A.4a) |
| `:3` XFCE | session 11177, xfwm 11216, panel 11371, desktop 11419, terminal 11235 — still alive |
| APK | `com.waydefu.x11gpu` `1.03.01-6182b94-07.09.26` |
| commit | `6182b94bc69166e49a2f6ca0238ffdba9781fc68` |

A.4a–A.4d evidence **kept**. `:3` XFCE left running after the bounded observe (not killed; `:1` not touched).

---

## Verdict

**PASS.** XFCE/xfwm stayed up. `:3` still 32075. Probe recursion still 0; enter≈return. No SIGILL/SIGSEGV. `:1` still 26474. Desktop Composite (including the original 5×24 shape and full-screen dest) returned on the install-once probe build.

P2-A.4 repair (probe install-once) is sufficient for both the 1×1 crash repro and a bounded XFCE Composite session on :3.

Did **not** treat this as A.3 reopening. Did **not** patch pitch/sys_ptr. No commit.
