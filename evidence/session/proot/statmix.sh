#!/bin/bash
# STAT-MIX: stat-heavy work (git status / find / stat storm) + the per-call micro-benchmark.
R=/root/projects/GPU加速/src/f8-ahb-exa-async
blk() { local name=$1 n=$2; shift 2; local s=$(date +%s%N); for i in $(seq 1 $n); do "$@" >/dev/null 2>&1; done; printf "%-12s %6d ms\n" "$name" $(( ($(date +%s%N) - s) / 1000000 )); }
blk git_status 10 git -C $R status --short
blk find_tree  10 find $R/tests -type f
blk stat_storm 3 python3 -c 'import os
for r, d, f in os.walk("/usr/lib/python3"):
    for x in f: os.stat(os.path.join(r, x))'
/root/build/proot-bench/sysbench2 | grep -E 'fstat|open\+close|futex'
