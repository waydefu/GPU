#!/data/data/com.termux/files/usr/bin/sh
B=/data/data/com.termux/files/home/build/proot-fast
cd /data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs || exit 1
export PROOT_L2S_DIR=/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/.l2s
one() { label=$1; bin=$2; ex=$3
  set --; while IFS= read -r a; do set -- "$@" "$a"; done < $B/proot-args.txt
  env -u LD_PRELOAD $ex "$bin" "$@" /usr/bin/env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/root /bin/bash /root/build/proot-bench/stat_smoke.sh 2>&1 | grep -v "can't sanitize" > $B/v5smoke-$label.txt; }
one v2 $B/out2/bin/proot-fast2 ""
one v5b $B/out5b/bin/proot-fast5b ""

for l in v5b; do diff $B/v5smoke-v2.txt $B/v5smoke-$l.txt > $B/v5smoke-diff-$l.txt && echo "$l IDENTICAL to v2 ($(wc -l < $B/v5smoke-v2.txt) lines)" || { echo "$l DIFFERS"; head -20 $B/v5smoke-diff-$l.txt; }; done
