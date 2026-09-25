#!/data/data/com.termux/files/usr/bin/sh
# v2 / v5 / v6 / v6 with PROOT_STAT_AT_ENTER=0 (control, must equal v2), twice interleaved. Wall + total CPU.
B=/data/data/com.termux/files/home/build/proot-fast
cd /data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs || exit 1
export PROOT_L2S_DIR=/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/.l2s
one() { label=$1; bin=$2; ex=$3
  set --; while IFS= read -r a; do set -- "$@" "$a"; done < $B/proot-args.txt
  echo "== $label"; s=$(date +%s%N)
  env -u LD_PRELOAD $ex sh -c '"$0" "$@"; times' "$bin" "$@" /usr/bin/env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/root /bin/bash -c '/root/build/proot-bench/statxloop 20000; /root/build/proot-bench/statloop 20000; /root/build/proot-bench/statxmix.sh; /root/build/proot-bench/statmix.sh; /root/build/proot-bench/agentmix.sh' 2>&1 | grep -v "can't sanitize"
  echo "wall_total_ms $(( ($(date +%s%N) - s) / 1000000 ))"; }
for i in 1 2; do
  one "v2#$i" $B/out2/bin/proot-fast2 ""; one "v5#$i" $B/out5/bin/proot-fast5 ""; one "v6#$i" $B/out6/bin/proot-fast6 ""
  one "v6off#$i" $B/out6/bin/proot-fast6 PROOT_STAT_AT_ENTER=0
done
echo V6BENCH_DONE
