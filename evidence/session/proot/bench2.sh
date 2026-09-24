#!/data/data/com.termux/files/usr/bin/sh
# proot-fast v2 micro-benchmark: same 42 daily arguments, command = sysbench2. stock, v1, v2, and v2 with
# PROOT_KOMPAT_FULL=1 (the control that must be slow again for futex/epoll_pwait/fcntl, vdso absent). Twice each.
B=/data/data/com.termux/files/home/build/proot-fast
cd /data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs || exit 1
export PROOT_L2S_DIR=/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/.l2s
run() { label=$1; bin=$2; shift 2
  set --; while IFS= read -r a; do set -- "$@" "$a"; done < $B/proot-args.txt
  echo "== $label"; env -u LD_PRELOAD $EXTRA "$bin" "$@" /root/build/proot-bench/sysbench2 2>&1 | grep -v "can't sanitize"; }
for i in 1 2; do
  EXTRA= run "stock#$i" /data/data/com.termux/files/usr/bin/proot
  EXTRA= run "fast1#$i" $B/out/bin/proot-fast
  EXTRA= run "fast2#$i" $B/out2/bin/proot-fast2
  EXTRA=PROOT_KOMPAT_FULL=1 run "fast2+kompatfull#$i" $B/out2/bin/proot-fast2
done
