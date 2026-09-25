#!/bin/bash
# proot-fast v5 functional check for the stat family: output must be identical under v2, v5 and v5 with PROOT_STAT_AT_ENTER=0.
D=/root/build/proot-bench/statsmoke; rm -rf $D; mkdir -p $D/dir; cd $D
echo data > file; ln file hard; ln -s file sym; ln -s missing dangling; chmod 640 file; mkdir -p dir/sub; touch dir/sub/x
st() { stat -c '%n|%U:%G|%a|%h|%s|%F' "$@" 2>&1 | sed 's/[0-9]\{6,\}/N/g'; echo "rc=$?"; }
st file hard dir sym; st -L sym; st dangling; st -L dangling; st missing
(cd dir && st sub sub/x ../file)
st /dev/null /tmp /proc/self/status | sed 's/|[0-9]*|/|S|/'
python3 - <<'PY'
import os, stat
for p, follow in (("file", True), ("hard", True), ("sym", False), ("sym", True), ("dangling", False), ("dir/sub/x", True)):
    s = os.stat(p, follow_symlinks=follow)
    print("py", p, follow, s.st_uid, s.st_gid, oct(s.st_mode), s.st_nlink, s.st_size)
for p in ("dangling", "missing"):
    try: os.stat(p); print("py", p, "ok?")
    except OSError as e: print("py", p, e.errno, e.strerror)
PY
python3 - <<'PY'
import os, socket
def show(tag, fd):
    s = os.fstat(fd); print("fstat", tag, s.st_uid, s.st_gid, oct(s.st_mode), s.st_nlink, s.st_size if tag != "pipe" else "-")
f = open("hard"); show("hardlink", f.fileno())
g = open("dir/sub/x"); show("file", g.fileno())
d = os.open("dir", os.O_RDONLY); show("dirfd", d)
r, w = os.pipe(); show("pipe", r)
a, b = socket.socketpair(); show("socket", a.fileno())
n = os.open("/dev/null", os.O_RDONLY); show("devnull", n)
t = open("gone", "w"); t.write("x"); t.flush(); os.unlink("gone"); show("deleted", t.fileno())
print("fstat bad", end=" ")
try: os.fstat(9999)
except OSError as e: print(e.errno)
PY
node -e 'const fs=require("fs"); for (const p of ["file","hard","dir"]) { const s=fs.statSync(p); console.log("node", p, s.uid, s.gid, s.nlink, s.size) } const l=fs.lstatSync("sym"); console.log("node lstat sym", l.isSymbolicLink())'
ls -la | awk '{print $1, $2, $3, $4, $9, $10, $11}' | tail -n +2
find . | sort
cd /root/projects/GPU加速/src/f8-ahb-exa-async && git status --short tests/proot | head -3; echo "git rc=$?"
git -C /root/projects/GPU加速/src/f8-ahb-exa-async rev-parse --is-inside-work-tree
echo STAT_SMOKE_DONE
