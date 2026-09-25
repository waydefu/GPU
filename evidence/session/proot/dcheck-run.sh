#!/data/data/com.termux/files/usr/bin/sh
B=/data/data/com.termux/files/home/build/proot-fast
cd /data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs || exit 1
export PROOT_L2S_DIR=/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/.l2s
one() { label=$1; bin=$2; ex=$3
  set --; while IFS= read -r a; do set -- "$@" "$a"; done < $B/proot-args.txt
  env -u LD_PRELOAD $ex "$bin" "$@" /usr/bin/env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/root /bin/bash /root/build/proot-bench/daily_check.sh 2>&1 | grep -v "can't sanitize" > $B/dcheck-$label.txt; }
one v2 $B/out2/bin/proot-fast2 ""
one v5 $B/out5/bin/proot-fast5 ""

for l in v5; do diff $B/dcheck-v2.txt $B/dcheck-$l.txt > $B/dcheck-diff-$l.txt && echo "$l IDENTICAL to v2 ($(wc -l < $B/dcheck-v2.txt) lines)" || { echo "$l DIFFERS"; head -20 $B/dcheck-diff-$l.txt; }; done
