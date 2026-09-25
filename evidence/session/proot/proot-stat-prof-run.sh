#!/data/data/com.termux/files/usr/bin/sh
# proftrace the proot tracer while the guest runs N fstat (and, second, N futex-free getpid as the untrapped control).
B=/data/data/com.termux/files/home/build/proot-fast
cd /data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs || exit 1
export PROOT_L2S_DIR=/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/.l2s
set --; while IFS= read -r a; do set -- "$@" "$a"; done < $B/proot-args.txt
rm -f $B/prof-*.out
for n in 0 20000; do
  env -u LD_PRELOAD LD_PRELOAD=$B/libproftrace.so PROFTRACE_OUT=$B/prof-$n.out $B/out2/bin/proot-fast2 "$@" \
    /usr/bin/env -i PATH=/usr/bin:/bin /root/build/proot-bench/fstatloop $n 2>&1 | grep -v "can't sanitize\|preloaded"
  echo "== n=$n"; cat $B/prof-$n.out
done
