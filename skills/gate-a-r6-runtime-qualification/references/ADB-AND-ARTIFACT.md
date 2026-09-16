# ADB and artifact traps — Gate A R6

Authority binary: `/data/data/com.termux/files/usr/bin/adb` (ARM64 35.0.2).
`/usr/local/bin/f8-adb-port` is invalid under PRoot.

## Isolated lane

- Listener: `-L tcp:5038 server nodaemon` (not `-L tcp:127.0.0.1:5038`).
- Clients: `-H 127.0.0.1 -P 5038 -s HOST:PORT`.
- Never touch 5037. Never start a second 5038 server if one is alive.
- Stale pidfile with dead PID: document, remove, then start one nodaemon.
- Key: `HOME=/data/data/com.termux/files/home`. Wrong HOME → TLS
  `CERTIFICATE_UNKNOWN` (reject endpoint; do not retry the same one).
- Command is `server-status` (hyphen). `server status` tries to spawn a
  hostname-bound listener and fails with
  `listening on specified hostname currently unsupported`.

## Serial

Live-fetch `_adb-tls-connect._tcp.local.` via
`evidence/session/gate-a-a1/runtime/mdns-address.py`. Do not hardcode the last
IP:port. Identity after connect: `ro.product.device=myron`, screen Awake,
keyguard false.

## Install

Use the dated `install-<sha>.sh` with `RUN_INSTALL=YES`. Kill experimental X
only if cmdline starts with `termux-x11gpu com.waydefu.x11gpu :3`. Force-stop
`com.waydefu.x11gpu` before `pm install-commit`. Bind local SHA = staged SHA =
pulled installed-base SHA = expected SHA, and installed arm64 Build ID.

## Artifact

- Download APK + unstripped from the **same** `workflow_dispatch` run.
- GitHub artifact `digest` is the ZIP wrapper, not APK bytes.
- Expected experimental signer:
  `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1`.
- Formal `zipalign` on this host is x86-64; do not claim zipalign PASS.
- nm filters that only match `gateA` miss `present_gpu_copy_retire_or_fatal`.
