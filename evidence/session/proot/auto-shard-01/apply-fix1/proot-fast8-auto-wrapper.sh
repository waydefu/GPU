#!/data/data/com.termux/files/usr/bin/sh
# proot-fast8 with automatic shards on (AUTO-SHARD-01, 2026-09-26). proot-distro hands proot only PROOT_NO_SECCOMP,
# PROOT_VERBOSE and PROOT_L2S_DIR from the caller's environment (login/__init__.py), so an export in f8desk never
# reaches proot; the switch is set here, right before the real binary. Same basename as the binary on purpose:
# proot-distro recognises its sessions by /proc/<pid>/comm == basename of PD_PROOT_BIN, and after the exec below
# comm is "proot-fast8" (the pid stays the same).
export PROOT_F8_AUTOSHARD=1
export PROOT_F8_AUTOSHARD_LOG=/data/data/com.termux/files/usr/tmp/f8-shard/autoshard.log
exec /data/data/com.termux/files/home/build/proot-fast/out8/bin/proot-fast8 "$@"
