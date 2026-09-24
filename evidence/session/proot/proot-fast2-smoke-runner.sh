#!/data/data/com.termux/files/usr/bin/sh
B=/data/data/com.termux/files/home/build/proot-fast
cd /data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs || exit 1
export PROOT_L2S_DIR=/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/.l2s
for v in stock fast2; do
  [ $v = stock ] && bin=/data/data/com.termux/files/usr/bin/proot || bin=$B/out2/bin/proot-fast2
  set --; while IFS= read -r a; do set -- "$@" "$a"; done < $B/proot-args.txt
  env -u LD_PRELOAD "$bin" "$@" /usr/bin/env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/root /bin/bash /root/build/proot-bench/smoke.sh > $B/smoke-$v.txt 2>&1
done
diff $B/smoke-stock.txt $B/smoke-fast2.txt && echo SMOKE_IDENTICAL; wc -l < $B/smoke-fast2.txt
