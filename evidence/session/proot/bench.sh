#!/data/data/com.termux/files/usr/bin/sh
# Same 42 arguments as the live desktop proot (pid 20095, proot-distro ubuntu), command replaced by the
# socket/pipe micro-benchmark. Runs stock proot, proot-fast, and proot-fast with PROOT_BWRAP_COMPAT=1
# (the control that must be slow again). Each twice. Nothing is installed or replaced.
B=/data/data/com.termux/files/home/build/proot-fast
cd /data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs || exit 1
export PROOT_L2S_DIR=/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/.l2s
run() { # label proot-binary [ENV=VAL]
  label=$1; bin=$2; shift 2
  set --
  while IFS= read -r a; do set -- "$@" "$a"; done < $B/proot-args.txt
  echo "== $label"
  env -u LD_PRELOAD $EXTRA "$bin" "$@" /root/build/proot-bench/sysbench 2>&1 | grep -v "can't sanitize"
}
for i in 1 2; do
  EXTRA= run "stock#$i" /data/data/com.termux/files/usr/bin/proot
  EXTRA= run "fast#$i" $B/out/bin/proot-fast
  EXTRA=PROOT_BWRAP_COMPAT=1 run "fast+compat#$i" $B/out/bin/proot-fast
done
