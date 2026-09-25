#!/data/data/com.termux/files/usr/bin/sh
# v7 correctness (TRACER-SHARD): stat_smoke / smoke / daily_check under v6 (reference), v7, and the broken v6b (must differ).
B=/data/data/com.termux/files/home/build/proot-fast
cd /data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs || exit 1
export PROOT_L2S_DIR=/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/.l2s
set --; while IFS= read -r a; do set -- "$@" "$a"; done < $B/proot-args.txt
for t in stat_smoke smoke daily_check; do
  for v in v6:$B/out6/bin/proot-fast6: v7:$B/out7/bin/proot-fast7: v6b:$B/out6b/bin/proot-fast6b:; do
    l=${v%%:*}; r=${v#*:}; bin=${r%%:*}; ex=${r#*:}
    env -u LD_PRELOAD $ex "$bin" "$@" /usr/bin/env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/root /bin/bash /root/build/proot-bench/$t.sh 2>&1 | grep -v "can't sanitize" > $B/v7c-$t-$l.txt
  done
  for l in v7 v6b; do diff -q $B/v7c-$t-v6.txt $B/v7c-$t-$l.txt >/dev/null && echo "$t $l IDENTICAL ($(wc -l < $B/v7c-$t-v6.txt) lines)" || echo "$t $l DIFFERS ($(diff $B/v7c-$t-v6.txt $B/v7c-$t-$l.txt | grep -c '^[<>]') changed lines)"; done
done
echo V7CHECK_DONE
