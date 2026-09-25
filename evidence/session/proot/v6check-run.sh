#!/data/data/com.termux/files/usr/bin/sh
# v6 correctness: stat_smoke / smoke / daily_check under v2 (reference), v6, v6 with PROOT_STAT_AT_ENTER=0, and the broken v6b (must differ).
B=/data/data/com.termux/files/home/build/proot-fast
cd /data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs || exit 1
export PROOT_L2S_DIR=/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/.l2s
set --; while IFS= read -r a; do set -- "$@" "$a"; done < $B/proot-args.txt
for t in stat_smoke smoke daily_check; do
  for v in v2:$B/out2/bin/proot-fast2: v6:$B/out6/bin/proot-fast6: v6off:$B/out6/bin/proot-fast6:PROOT_STAT_AT_ENTER=0 v6b:$B/out6b/bin/proot-fast6b:; do
    l=${v%%:*}; r=${v#*:}; bin=${r%%:*}; ex=${r#*:}
    env -u LD_PRELOAD $ex "$bin" "$@" /usr/bin/env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/root /bin/bash /root/build/proot-bench/$t.sh 2>&1 | grep -v "can't sanitize" > $B/v6c-$t-$l.txt
  done
  for l in v6 v6off v6b; do diff -q $B/v6c-$t-v2.txt $B/v6c-$t-$l.txt >/dev/null && echo "$t $l IDENTICAL ($(wc -l < $B/v6c-$t-v2.txt) lines)" || echo "$t $l DIFFERS ($(diff $B/v6c-$t-v2.txt $B/v6c-$t-$l.txt | grep -c '^[<>]') changed lines)"; done
done
