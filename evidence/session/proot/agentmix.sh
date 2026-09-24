#!/bin/bash
# AGENT-MIX: the kind of work an AI coding agent's tool calls do (git, grep, find, python/node startups, small scripts).
R=/root/projects/GPU加速/src/f8-ahb-exa-async; E=/root/projects/GPU加速/evidence/session
t() { local s=$(date +%s%N); "$@" >/dev/null 2>&1; echo $(( ($(date +%s%N) - s) / 1000000 )); }
blk() { local name=$1; shift; local s=$(date +%s%N); for i in $(seq 1 $N); do "$@" >/dev/null 2>&1; done; printf "%-14s %6d ms\n" "$name" $(( ($(date +%s%N) - s) / 1000000 )); }
N=10
blk git_status   git -C $R status --short
blk git_log      git -C $R log -30 --stat
blk grep_tree    grep -rn --include=*.md kompat $E/proot
blk find_tree    find $R/tests -type f -name '*.py'
blk python_start python3 -c 'import json, re, subprocess, pathlib, threading'
blk node_start   node -e 'require("fs"); require("child_process")'
blk bash_pipes   bash -c 'for i in $(seq 1 50); do echo $i; done | sort -n | tail -1 | wc -c'
blk py_threads   python3 -c 'import threading; l=threading.Lock(); n=[0]
def w():
    for _ in range(20000):
        with l: n[0]+=1
ts=[threading.Thread(target=w) for _ in range(4)]; [t.start() for t in ts]; [t.join() for t in ts]'
blk node_async   node -e 'let n=0; const tick=()=>{ if(++n<20000) setImmediate(tick) }; tick()'
