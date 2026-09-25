#!/data/data/com.termux/files/usr/bin/sh
B=/data/data/com.termux/files/home/build/proot-fast
cd /data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs || exit 1
export PROOT_L2S_DIR=/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/.l2s
one() { label=$1; bin=$2; ex=$3
  set --; while IFS= read -r a; do set -- "$@" "$a"; done < $B/proot-args.txt
  echo "== $label"; env -u LD_PRELOAD $ex "$bin" "$@" /usr/bin/env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/root /bin/bash /root/build/proot-bench/netcheck.sh 2>&1 | grep -v "can't sanitize"; }
one stock /data/data/com.termux/files/usr/bin/proot ""
one v2 $B/out2/bin/proot-fast2 ""
one v3 $B/out3/bin/proot-fast3 ""
one v3+bwrapcompat $B/out3/bin/proot-fast3 PROOT_BWRAP_COMPAT=1
