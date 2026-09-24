#!/data/data/com.termux/files/usr/bin/sh
# AGENT-MIX under stock proot / proot-fast2 / proot-fast2+PROOT_KOMPAT_FULL (control). Descriptive, not a gate.
B=/data/data/com.termux/files/home/build/proot-fast
cd /data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs || exit 1
export PROOT_L2S_DIR=/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/.l2s
one() { label=$1; bin=$2; ex=$3
  set --; while IFS= read -r a; do set -- "$@" "$a"; done < $B/proot-args.txt
  echo "== $label"
  s=$(date +%s%N)
  env $ex sh -c 'env -u LD_PRELOAD "$0" "$@"; times' "$bin" "$@" /usr/bin/env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/root /bin/bash /root/build/proot-bench/agentmix.sh 2>&1 | grep -v "can't sanitize"
  echo "wall_total_ms $(( ($(date +%s%N) - s) / 1000000 ))"
}
for i in 1 2; do
  one "stock#$i" /data/data/com.termux/files/usr/bin/proot ""
  one "fast2#$i" $B/out2/bin/proot-fast2 ""
done
one "fast2+kompatfull" $B/out2/bin/proot-fast2 PROOT_KOMPAT_FULL=1
