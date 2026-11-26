#!/data/data/com.termux/files/usr/bin/sh
# Native Termux build of proot 5.1.107.92 + proot-fast-bwrap-compat.patch + kompat-lean + stat-at-enter + statx (v6) + peercred mapping for same-uid non-tracee peers (v7, TRACER-SHARD) + auto-shard of Electron/terminal execve (v8, AUTO-SHARD), same flags as the Termux package
# (termux-packages 08b49b3ce0) except VERSION suffix and a private loader dir.
set -e
B=/data/data/com.termux/files/home/build/proot-fast
cd $B/proot-5.1.107.92-v8
make -C src clean >/dev/null 2>&1 || true
# CPPFLAGS through the environment (the makefile appends to it); on the make command line it would
# replace the makefile's own -I flags (first build attempt failed exactly like that).
CPPFLAGS='-DARG_MAX=131072 -DVERSION=\"5.1.107.92-fast8\"' \
make -C src proot CC=clang OBJCOPY=llvm-objcopy PROOT_WITH_LIBANDROID_SHMEM=true \
  PROOT_UNBUNDLE_LOADER=$B/out8/libexec -j2 > $B/build8.log 2>&1
mkdir -p $B/out8/bin $B/out8/libexec
cp src/proot $B/out8/bin/proot-fast8
cp src/loader/loader $B/out8/libexec/loader
[ -f src/loader/loader-m32 ] && cp src/loader/loader-m32 $B/out8/libexec/loader32 || true
echo BUILD_OK
