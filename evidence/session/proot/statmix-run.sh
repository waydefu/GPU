#!/data/data/com.termux/files/usr/bin/sh
# v2 vs v4 with PROOT_SPIN_US = 0 (control: must equal v2) / 20 / 50 / 100 / 200, twice, interleaved. Wall + total CPU.
B=/data/data/com.termux/files/home/build/proot-fast
cd /data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs || exit 1
export PROOT_L2S_DIR=/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/.l2s
one() { label=$1; bin=$2; spin=$3
  set --; while IFS= read -r a; do set -- "$@" "$a"; done < $B/proot-args.txt
  echo "== $label"; s=$(date +%s%N)
  env -u LD_PRELOAD PROOT_SPIN_US=$spin sh -c '"$0" "$@"; times' "$bin" "$@" /usr/bin/env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/root /bin/bash /root/build/proot-bench/statmix.sh 2>&1 | grep -v "can't sanitize"
  echo "wall_total_ms $(( ($(date +%s%N) - s) / 1000000 ))"; }
for i in 1 2; do
  one "v2#$i" $B/out2/bin/proot-fast2 0
  for sp in 0 20 50 100 200; do one "v4-spin$sp#$i" $B/out4/bin/proot-fast4 $sp; done
done
