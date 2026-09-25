#!/bin/bash
# Daily-use check for proot-fast (v2 vs v5): network interfaces, venv, local git clone (hardlinks -> link2symlink),
# fsck/status, tar with hardlinks, find -links, cp -a, apt simulate. Output must be identical across versions.
W=/root/build/proot-bench/dailycheck; rm -rf $W; mkdir -p $W; cd $W
node -e 'const n=require("os").networkInterfaces(); console.log("node_ifaces", Object.keys(n).sort().join(","))' 2>&1
python3 -m venv venv >/dev/null 2>&1; echo "venv rc=$? $(venv/bin/python -c 'import sys; print(sys.prefix != sys.base_prefix)')"
git init -q src && cd src && for i in 1 2 3; do echo "line $i" > f$i.txt; done && git add . && git -c user.name=t -c user.email=t@t commit -qm init && cd ..
git clone -q --local src clone; echo "clone rc=$?"; (cd clone && git fsck --no-progress 2>&1 | tail -2; echo "fsck rc=$?"; git status --short | wc -l; git log --oneline | wc -l)
obj=$(cd clone && git rev-parse HEAD:f1.txt); o=clone/.git/objects/${obj:0:2}/${obj:2}; stat -c 'clone_obj_nlink=%h' "$o" 2>/dev/null || echo "clone_obj packed"
mkdir t && echo hello > t/a && ln t/a t/b && tar -cf t.tar t && rm -rf t && tar -xf t.tar && stat -c '%n %h' t/a t/b && find t -links 2 | sort
cp -a t t2 && stat -c '%n %h %U' t2/a t2/b
apt-get -s install sl 2>&1 | grep -cE '^Inst|is already the newest' | sed 's/^/apt_sim_lines=/'
python3 -c "import os, pathlib; print('py_rglob', sum(1 for _ in pathlib.Path('/usr/lib/python3/dist-packages').rglob('*.py')) > 100)"
echo DAILY_CHECK_DONE
