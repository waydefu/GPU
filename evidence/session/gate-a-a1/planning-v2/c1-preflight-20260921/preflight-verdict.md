# R8-C1 PREFLIGHT — 2026-09-21

SCOPE     host-only + device READ-ONLY. No device mutation. No attempt consumed.
STATE     attempt-09 directory ABSENT. GRANT NOT GIVEN. Runner NOT invoked.
VERDICT   ALL GREEN — ready for explicit grant

## Lane
```
isolated server   PID 31008  adb -L tcp:5038        (5037 PID 31022 untouched throughout)
discovery         _adb-tls-connect._tcp.local. -> 192.168.1.100:37985   [freshly resolved]
SERIAL            192.168.1.100:37985
                  snapshot 10.191.48.13:46847 NOT reused (report-only, per §2.5)
                  frozen failed 10.191.48.13:45165 NOT contacted (different subnet)
client form       adb -H 127.0.0.1 -P 5038 -s <SERIAL>     (V-7R / P008 bound form)
key               HOME=/data/data/com.termux/files/home    (TLS fingerprint matched, no CERT_UNKNOWN)
```

## Results
| group | item | result |
|---|---|---|
| ADB | 1 mdns resolve, fresh | PASS |
| ADB | 2 isolated 5038, 5037 untouched | PASS |
| ADB | 3 SERIAL runtime-discovered | PASS |
| ADB | 4 frozen failed endpoint not contacted | PASS |
| ADB | 5 **SERIAL verbatim in `devices`** (V-23 / R-27) | PASS |
| ADB | 6 `ro.product.device` == myron | PASS |
| SCREEN | mWakefulness=Awake | PASS |
| SCREEN | isKeyguardShowing=false | PASS |
| STABLE | com.termux.x11 present, versionName 1.03.01-11b82d9-06.09.26 | PASS |
| STABLE | PID **8430** runtime-discovered (NOT the stale 20146 snapshot; R-29) | PASS |
| STABLE | cmdline == `termux-x11 com.termux.x11 :1 -legacy-drawing` | PASS |
| X3 | no `:3` process (runner `x3pid()` logic) | PASS |
| X3 | no X3 socket, no X3 lock | PASS |
| ARTIFACT | versionName == 1.03.01-b984ded-18.09.26 | PASS |
| ARTIFACT | **installed APK sha256 == 0d06de68…d398d3** | PASS |
| ARTIFACT | SIGNER b6da0148…, BUILD_ID 3658dd1f… | PASS (transitive, see note) |
| FIXTURE | /tmp/p_r8_lifecycle == ad93f2ba…f12de | PASS (rebuilt via f8-r8-fixture) |

## Findings this round

### F1 — runner verifies versionName ONLY
`run-r8-one-cell-b984ded-v2.sh` L151 checks `versionName`. `EXPECT_APK_SHA256`,
`EXPECT_BUILD_ID` and `EXPECT_SIGNER` are written into `artifact-binding.json`
(L96-L107) but are **never compared against the device**. §22.5 ARTIFACT_PRECHECK
demands all four. Without an operator check, `artifact-binding.json` would assert
values nobody verified -- narrative presented as evidence.
Closed here by direct readback: `sha256sum $(pm path com.waydefu.x11gpu)` on device
== `0d06de68…d398d3` exactly. Because the full APK is byte-identical to the pinned
artifact, its embedded signing certificate and build id are necessarily the pinned
ones -- SIGNER and BUILD_ID are transitively proven, not assumed.
**Recommend: fold these three comparisons into the runner.**

### F2 — R-29 is a documentation defect only; the runner is immune
`stable_json()` runs `pid=$(stabpid)` (runtime discovery) and asserts only the
cmdline prefix. It never compares 20146. Only §22.5's prose hardcoded the PID.
Measured today: Stable is healthy at PID 8430. Plan text fixed in V2.3.

### F3 — `pgrep -f` self-match is a live false-BLOCK trap for X3_PRECHECK
A hand-run `pgrep -f 'termux-x11gpu com.waydefu.x11gpu :3'` matches the operator's
OWN shell, because the pattern appears in that shell's command line. It reported a
phantom residual `:3` here. The runner's `x3pid()` is immune (it compares each
`/proc/*/cmdline` by exact prefix). **X3_PRECHECK must use the `x3pid()` form; never
a bare `pgrep -f`.**
