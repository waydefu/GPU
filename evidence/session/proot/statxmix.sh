#!/bin/bash
# STATX-MIX: statx-heavy work (coreutils ls -l, Node fs.statSync walk).
blk() { local name=$1 n=$2; shift 2; local s=$(date +%s%N); for i in $(seq 1 $n); do "$@" >/dev/null 2>&1; done; printf "%-12s %6d ms\n" "$name" $(( ($(date +%s%N) - s) / 1000000 )); }
blk ls_laR 3 ls -laR /usr/lib/python3/dist-packages
blk node_walk 3 node -e 'const fs=require("fs"),p=require("path");let n=0;(function w(d){for(const e of fs.readdirSync(d)){const f=p.join(d,e);const s=fs.lstatSync(f);n++;if(s.isDirectory())w(f)}})("/usr/lib/python3/dist-packages")'
