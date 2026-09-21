# GATE A P2 R8 2a245b0 INSTALL BIND BLOCKED — 2026-09-18

```
STATUS: R8_INSTALL_BIND_BLOCKED
        ADB devices empty
        mDNS _adb-tls-connect._tcp empty
        last-known 10.191.48.13 ICMP unreachable
        experimental remains 5a782f6 INSTALLED
        attempt-06 NOT RUN
        Production Gate A BLOCKED
```

Isolated ADB 5038 server PID **3065** is alive (`adb -L tcp:5038 server nodaemon`).
`adb -H 127.0.0.1 -P 5038 devices` listed nothing.
`mdns-address.py` and an 8s Zeroconf browse returned zero endpoints.
Workstation `wlan0` is `192.168.1.100/24`; ping of historical serial host `10.191.48.13` failed.
No CERT_UNKNOWN retry. No second 5038 server. Stable `:1` not touched.

Install script ready: `p2-r8-runtime/install-2a245b0.sh` (REFUSE unless `RUN_INSTALL=YES` and CELL `.../runtime-2a245b0/r0`).
Runner ready: `p2-r8-runtime/run-r8-one-cell-2a245b0.sh` (`VALIDATE_ONLY=1` PASS).

Do **not** create `runtime-2a245b0/r8-c1/attempt-06-*` until install bind PASS.
Do **not** retry C1 attempts 01–05.
