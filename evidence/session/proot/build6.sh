#!/data/data/com.termux/files/usr/bin/sh
# Native Termux build of proot 5.1.107.92 + proot-fast-bwrap-compat.patch + kompat-lean + stat-at-enter + statx (v6), same flags as the Termux package
# (termux-packages 08b49b3ce0) except VERSION suffix and a private loader dir.
set -e
B=/data/data/com.termux/files/home/build/proot-fast
cd $B/proot-5.1.107.92-v6
make -C src clean >/dev/null 2>&1 || true
# CPPFLAGS through the environment (the makefile appends to it); on the make command line it would
# replace the makefile's own -I flags (first build attempt failed exactly like that).
CPPFLAGS='-DARG_MAX=131072 -DVERSION=\"5.1.107.92-fast6\"' \
make -C src proot CC=clang OBJCOPY=llvm-objcopy PROOT_WITH_LIBANDROID_SHMEM=true \
  PROOT_UNBUNDLE_LOADER=$B/out6/libexec -j2 > $B/build6.log 2>&1
mkdir -p $B/out6/bin $B/out6/libexec
cp src/proot $B/out6/bin/proot-fast6
cp src/loader/loader $B/out6/libexec/loader
[ -f src/loader/loader-m32 ] && cp src/loader/loader-m32 $B/out6/libexec/loader32 || true
echo BUILD_OK
