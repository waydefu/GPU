#!/usr/bin/env python3
"""Stage 7.6 isolated device security run (gates S1-S7, docs/F8-HYBRID2-STAGE76-FREEZE-20261128.md).

Runs inside PRoot. Builds its own run directory (scripts copy, budget, socket, fixture repo written
by PRoot git, outside secrets), starts its own native daemon through termux-bg-run, and never touches
the deployed pilot. Native-side mutations (object link swaps) run in the native helper, because a
rename inside PRoot over a link2symlink name changes PRoot's link-count bookkeeping.

Usage: stage76_security.py PARENT_DIR [--only S1,S2,...]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zlib
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import f8_hybrid2_budget as budget  # noqa: E402
from stage75_matrix import descendants  # noqa: E402

RUNNER = "/usr/local/bin/termux-bg-run"
TPY = "/data/data/com.termux/files/usr/bin/python3"
ROOTFS = "/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs"
L2S = ROOTFS + "/.l2s"
PILOT = Path("/data/data/com.termux/files/home/build/proot-fast/tools/hybrid2")
MARKER = "S76-SECRET-MARKER-7d1c"
MARKER2 = "S76-OUTSIDE-OBJECT-MARKER-55af"
D1_CMDS = (["log", "-n", "20", "--stat"], ["show", "--stat", "HEAD"], None,  # None = cat-file -p <l2s oid>
           ["rev-list", "--count", "HEAD"], ["ls-tree", "-r", "--name-only", "HEAD"])

HELPER = r'''
import json, os, sys, time, hashlib
args = json.load(open(sys.argv[1]))
out = {}
def swap(path, target):
    tmp = path + ".s76tmp"
    try: os.unlink(tmp)
    except FileNotFoundError: pass
    os.symlink(target, tmp); os.replace(tmp, path)
act = args["action"]
if act == "readlink":
    out["targets"] = {p: os.readlink(p) for p in args["paths"]}
elif act == "point":
    swap(args["path"], args["target"]); out["now"] = os.readlink(args["path"])
elif act == "forge":
    d = args["dir"]; os.makedirs(d, exist_ok=True)
    hop1 = os.path.join(d, args["name"]); hop2 = hop1 + ".0001"
    if args.get("final_dir"): os.mkdir(hop2)
    else: open(hop2, "w").write(args["content"])
    os.symlink(hop2, hop1); out["hop1"] = hop1; out["hop2"] = hop2
elif act == "unforge":
    for p in args["paths"]:
        if os.path.islink(p) or os.path.isfile(p): os.unlink(p)
        elif os.path.isdir(p): os.rmdir(p)
    out["removed"] = args["paths"]
elif act == "race":
    open(args["started"], "w").write("1")
    end = time.monotonic() + args["seconds"]; n = 0
    try:
        while time.monotonic() < end and not os.path.exists(args["stop"]):
            swap(args["path"], args["targets"][n % 2]); n += 1; time.sleep(0.0005)
    finally:
        swap(args["path"], args["targets"][0])
    out["swaps"] = n; out["restored"] = os.readlink(args["path"])
elif act == "pollkids":
    dpid = open(args["pidfile"]).read().strip(); open(args["started"], "w").write("1")
    best = {"pss_kib": None, "samples": 0, "seen": 0}; end = time.monotonic() + args["seconds"]
    while time.monotonic() < end and not os.path.exists(args["stop"]):
        for pid in os.listdir("/proc"):
            if not pid.isdigit(): continue
            try:
                if open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()[1] != dpid: continue
                roll = open(f"/proc/{pid}/smaps_rollup").read().split("\n")
                pss = int(next(l for l in roll if l.startswith("Pss:")).split()[1])
            except (OSError, StopIteration, ValueError, IndexError): continue
            best["seen"] += 1; best["pss_kib"] = max(best["pss_kib"] or 0, pss)
        best["samples"] += 1; time.sleep(0.001)
    out.update(best)
elif act == "policy_scan":
    sys.path.insert(0, args["scripts"])
    os.environ["F8_HYBRID2_TRUSTED_GIT_ROOTS"] = json.dumps(args["roots"])
    from f8_hybrid2_policy import Policy
    pol = Policy([("/root/projects", args["host_projects"])], home=args["home"], tmp=args["tmp"])
    times = {}
    for repo in args["repos"]:
        ts = []
        for _ in range(5):
            t = time.perf_counter(); pol.validate_git_ro(["status"], repo); ts.append((time.perf_counter() - t) * 1000)
        times[repo] = sorted(ts)
    out["scan_ms"] = times
json.dump(out, open(args["result"], "w"))
'''


def sh(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


class Run:
    def __init__(self, parent: Path) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="s76-sec.", dir=parent))
        self.results = self.dir / "s76-results.jsonl"
        self.nhelp = 0
        self.roots = json.loads((PILOT / "trusted-git-roots.json").read_text()) + ["/fixture"]

    def log(self, row: dict) -> None:
        row = {"ts": round(time.time(), 3), **row}
        with self.results.open("a") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(json.dumps(row, ensure_ascii=False)[:400], flush=True)

    # --- native side -------------------------------------------------------------------------
    def native(self, action: str, timeout: int = 60, background: bool = False, **args) -> dict | subprocess.Popen:
        self.nhelp += 1
        n = self.nhelp
        a = self.dir / f"helper-{n}.json"
        r = self.dir / f"helper-{n}.result.json"
        a.write_text(json.dumps({"action": action, "result": str(r), **args}))
        s = self.dir / f"helper-{n}.sh"
        s.write_text(f"#!/data/data/com.termux/files/usr/bin/bash\nexec {TPY} -B {self.dir}/native_helper.py {a}\n")
        s.chmod(0o700)
        cmd = [RUNNER, "--timeout", str(timeout), "--tail", "5", str(s)]
        if background:
            return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p = sh(cmd, timeout=timeout + 30)
        if p.returncode != 0 or not r.exists():
            raise RuntimeError(f"native helper {action} rc={p.returncode} {p.stdout[-300:]}")
        return json.loads(r.read_text())

    def prepare(self) -> None:
        d = self.dir
        (d / "scripts").mkdir()
        for f in HERE.glob("f8_hybrid2_*.py"):
            shutil.copy2(f, d / "scripts" / f.name)
        (d / "native_helper.py").write_text(HELPER)
        sh(["bash", "-c", f"cd {d}/scripts && sha256sum -- *.py > ../scripts.sha256"])
        (d / "candidate").write_text(sh(["git", "-C", str(HERE.parent), "rev-parse", "HEAD"]).stdout)
        (d / "candidate.dirty").write_text(sh(["git", "-C", str(HERE.parent), "status", "--porcelain", "--", "scripts"]).stdout)
        budget.init_budget_dir(str(d / "budget"), 4)
        budget.init_budget_dir(str(d / "budget6"), 4)
        for sub in ("r", "h", "outside", "ws3"):
            (d / sub).mkdir()
        (d / "outside/secret.txt").write_text(f"{MARKER} plaintext secret\n")
        (d / "outside/secret.json").write_text(json.dumps({"token": MARKER}) + "\n")
        (d / "outside/plain-secret").write_text(f"{MARKER} race target\n")
        ws = d / "ws"
        ws.mkdir()
        g = ["git", "-C", str(ws), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid"]
        sh(g[:3] + ["init", "-q"], check=True)
        for i in range(3):
            (ws / f"f{i}.txt").write_text(f"fixture file {i}\n" * (i + 1))
            sh(g + ["add", f"f{i}.txt"], check=True)
            sh(g + ["commit", "-qm", f"c{i}"], check=True)
        links = sh(["find", str(ws / ".git/objects"), "-type", "l"]).stdout.split()
        (d / "fixture-l2s-links").write_text(f"{len(links)}\n")
        if not links:
            raise RuntimeError("fixture has no l2s objects")
        roots_env = json.dumps(self.roots, ensure_ascii=False)
        (d / "run-daemon").write_text(f"""#!/data/data/com.termux/files/usr/bin/bash
set -eu
export PATH=/data/data/com.termux/files/usr/bin PYTHONDONTWRITEBYTECODE=1
export F8_HYBRID2_BUDGET_DIR={d}/budget
export F8_HYBRID2_TRUSTED_GIT_ROOTS='{roots_env}'
(cd {d}/scripts && sha256sum -c --quiet ../scripts.sha256)
grep -E '^(Uid|TracerPid):' /proc/self/status
setsid -f python3 {d}/scripts/f8_hybrid2_daemon.py --socket {d}/r/m.sock --pidfile {d}/r/d.pid --ready {d}/r/ready \\
  --log {d}/r/audit.jsonl --home {d}/h --tmp {d}/r --git-bin "$PATH/git" \\
  --map /root/projects={ROOTFS}/root/projects --map /fixture={ws} --map /ws3={d}/ws3 \\
  --max-clients 4 --max-inflight 8 >>{d}/r/daemon.out 2>&1 </dev/null
for _ in $(seq 100); do [ -e {d}/r/ready ] && exit 0; sleep 0.1; done
exit 8
""")
        (d / "run-daemon").chmod(0o700)

    def start_daemon(self) -> int:
        p = sh([RUNNER, "--timeout", "40", "--tail", "10", str(self.dir / "run-daemon")], timeout=70)
        if p.returncode != 0:
            raise RuntimeError(f"daemon start failed: {p.stdout[-400:]}")
        return int((self.dir / "r/d.pid").read_text().strip())

    def stop_daemon(self) -> None:
        sh([sys.executable, "-B", str(self.dir / "scripts/f8_hybrid2_ctl.py"), "--dir", str(self.dir / "r"), "stop"], timeout=30)

    # --- relay clients ----------------------------------------------------------------------
    def relay_env(self, fallback: bool, bdir: str | None = None) -> dict:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", F8_HYBRID2_BUDGET_DIR=bdir or str(self.dir / "budget"),
                   F8_HYBRID2_TRUSTED_GIT_ROOTS=json.dumps(self.roots, ensure_ascii=False))
        env.pop("F8_NO_HYBRID", None)
        if fallback:
            env["F8_NO_HYBRID"] = "1"
        return env

    def relay(self, fallback: bool, scripts: Path | None = None, extra: list[str] | None = None,
              bdir: str | None = None, sock: Path | None = None) -> "Client":
        scripts = scripts or (self.dir / "scripts")
        cmd = [sys.executable, "-B", str(scripts / "f8_hybrid2_relay.py"), "--socket", str(sock or self.dir / "r/m.sock"),
               "--map", "/root/projects=/root/projects", "--map", f"/fixture={self.dir}/ws", "--map", f"/ws3={self.dir}/ws3",
               *(extra or [])]
        return Client(subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       env=self.relay_env(fallback, bdir)))


class Client:
    def __init__(self, proc: subprocess.Popen) -> None:
        self.proc, self.n = proc, 0
        self.rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                "clientInfo": {"name": "s76", "version": "1"}})
        self.proc.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
        self.proc.stdin.flush()

    def rpc(self, method: str, params: dict) -> dict:
        self.n += 1
        self.proc.stdin.write((json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params}) + "\n").encode())
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError(f"relay closed: {self.proc.stderr.read()[-300:]!r}")
        return json.loads(line)

    def call(self, name: str, args: dict) -> tuple[dict, float]:
        t = time.perf_counter()
        r = self.rpc("tools/call", {"name": name, "arguments": args})
        ms = (time.perf_counter() - t) * 1000
        if "error" in r:
            return {"error": r["error"]["message"]}, ms
        res = r["result"]
        text = res["content"][0]["text"] if res.get("content") else ""
        try:
            body = json.loads(text)
        except ValueError:
            body = {"text": text}
        return ({**body, "isError": res.get("isError")}, ms)

    def close(self) -> tuple[int, str]:
        self.proc.stdin.close()
        rc = self.proc.wait(30)
        return rc, self.proc.stderr.read().decode(errors="replace")[-300:]


def git_view(r: dict) -> dict:
    if "error" in r:
        return {"error": r["error"]}
    return {k: r.get(k) for k in ("returncode", "stdout", "stderr", "truncated", "isError")}


def has_marker(obj, marker=MARKER) -> bool:
    return marker in json.dumps(obj, ensure_ascii=False)


def pct(v: list[float], p: int) -> float:
    v = sorted(v)
    return round(v[min(len(v) - 1, int(round(p / 100 * (len(v) - 1))))], 2)


# --- gates ------------------------------------------------------------------------------------
def s1(run: Run) -> dict:
    nat, fb = run.relay(False), run.relay(True)
    repos = []
    for root in run.roots:
        host = Path("/root/projects") if root.startswith("/root/projects") else None
        path = Path(root) if host else run.dir / "ws"
        kind = "repo" if (path / ".git").is_dir() else "worktree"
        links = sh(["find", str(path / ".git/objects"), "-type", "l"]).stdout.split() if kind == "repo" else []
        loose = [p for p in links if len(Path(p).name) == 38 and len(Path(p).parent.name) == 2]
        oid = (Path(loose[0]).parent.name + Path(loose[0]).name) if loose else sh(["git", "-C", str(path), "rev-parse", "HEAD"]).stdout.strip()
        cells = []
        for args in D1_CMDS:
            a = args or ["cat-file", "-p", oid]
            rn, tn = nat.call("git_ro", {"cwd": root, "args": a})
            rf, tf = fb.call("git_ro", {"cwd": root, "args": a})
            same = git_view(rn) == git_view(rf)
            cells.append({"args": a[:3], "same": same, "native": git_view(rn) if not same else {"returncode": rn.get("returncode"), "error": rn.get("error")},
                          "fallback_error": rf.get("error"), "native_ms": round(tn, 1), "fallback_ms": round(tf, 1)})
        ok_kind = all(c["same"] for c in cells) and (kind == "worktree" or all(c["native"].get("error") is None for c in cells))
        if kind == "worktree":  # erratum E1: any policy refusal, identical on both routes
            ok_kind = all(c["same"] and str(c["native"].get("error") or "").startswith("Policy refused:") for c in cells)
        row = {"gate": "S1", "repo": root, "kind": kind, "l2s_links": len(links), "pass": ok_kind, "cells": cells}
        run.log(row)
        repos.append(row)
    nat.close(); fb.close()
    with_l2s = [r for r in repos if r["kind"] == "repo" and r["l2s_links"] > 0]
    return {"gate": "S1", "pass": bool(with_l2s) and all(r["pass"] for r in repos),
            "repos_with_l2s": len(with_l2s), "repos": len(repos)}


def fixture_blob(run: Run, name: str = "f0.txt") -> tuple[str, Path, str]:
    ws = run.dir / "ws"
    oid = sh(["git", "-C", str(ws), "rev-parse", f"HEAD:{name}"]).stdout.strip()
    obj = ws / ".git/objects" / oid[:2] / oid[2:]
    target = run.native("readlink", paths=[str(obj)])["targets"][str(obj)]
    if not target.startswith(L2S + "/"):
        raise RuntimeError(f"fixture object is not an l2s link: {target}")
    return oid, obj, target


def s2(run: Run) -> dict:
    oid, obj, genuine = fixture_blob(run)
    nat = run.relay(False)
    base, _ = nat.call("git_ro", {"cwd": "/fixture", "args": ["cat-file", "-p", oid]})
    # (a) PRoot hard link of a non-git file
    hl = run.dir / "outside/secret-hl"
    os.link(run.dir / "outside/secret.txt", hl)
    hop_a = run.native("readlink", paths=[str(hl)])["targets"][str(hl)]
    forged_b = run.native("forge", dir=str(run.dir / "outside/forge"), name=".l2s.tmp_obj_Forge10001", content=f"{MARKER}\n")
    forged_c = run.native("forge", dir=L2S, name=".l2s.tmp_obj_S76Dir0001", final_dir=True)
    forged_d = run.native("forge", dir=L2S, name=".l2s.tmp_obj_S76Txt0001", content=f"{MARKER} not an object\n")
    cases = {"a-proot-hardlink-non-git": hop_a, "b-forged-chain-outside-l2s": forged_b["hop1"],
             "c-l2s-final-directory": forged_c["hop1"], "d-l2s-shape-plaintext(info)": forged_d["hop1"]}
    rows = {}
    try:
        for label, target in cases.items():
            run.native("point", path=str(obj), target=target)
            r, _ = nat.call("git_ro", {"cwd": "/fixture", "args": ["cat-file", "-p", oid]})
            rows[label] = {"target": target, "result": git_view(r), "marker": has_marker(r)}
            run.log({"gate": "S2", "case": label, **rows[label]})
    finally:
        run.native("point", path=str(obj), target=genuine)
        run.native("unforge", paths=[forged_c["hop1"], forged_c["hop2"], forged_d["hop1"], forged_d["hop2"]])
        hl.unlink()
    after, _ = nat.call("git_ro", {"cwd": "/fixture", "args": ["cat-file", "-p", oid]})
    nat.close()
    gated = [rows[k] for k in cases if not k.endswith("(info)")]
    ok = all("symlink-escape" in str(r["result"].get("error")) and not r["marker"] for r in gated)
    ok = ok and not rows["d-l2s-shape-plaintext(info)"]["marker"] and git_view(after) == git_view(base)
    return {"gate": "S2", "pass": ok, "restored_equal": git_view(after) == git_view(base)}


def s3_calls(c: Client) -> list[tuple[str, dict]]:
    calls = [("repo_text_search", {"root": "/ws3/evil-file", "pattern": MARKER, "fixed_string": True}),
             ("repo_text_search", {"root": "/ws3/evil-dir", "pattern": MARKER, "fixed_string": True}),
             ("repo_text_search", {"root": "/ws3", "pattern": MARKER, "fixed_string": True}),
             ("repo_tree_scan", {"root": "/ws3/evil-dir"}),
             ("repo_tree_scan", {"root": "/ws3", "compute_sha256": False}),
             ("python_json_summary", {"path": "/ws3/evil-dir/secret.json"}),
             ("git_ro", {"cwd": "/ws3/evil-dir", "args": ["status"]})]
    return [(n, c.call(n, a)[0]) for n, a in calls]


def s3(run: Run) -> dict:
    ws3, out = run.dir / "ws3", run.dir / "outside"
    (out / ".l2s.a0001").write_text(f"{MARKER} via l2s-named file\n")
    os.symlink(out / ".l2s.a0001", ws3 / "evil-file")
    os.symlink(out, ws3 / ".l2s.d0001")
    os.symlink(ws3 / ".l2s.d0001", ws3 / "evil-dir")
    (ws3 / "plain.txt").write_text("ordinary\n")
    old = run.dir / "old-scripts"
    old.mkdir()
    for f in (run.dir / "scripts").glob("f8_hybrid2_*.py"):
        blob = sh(["git", "-C", str(HERE.parent), "show", f"2050b19:scripts/{f.name}"])
        (old / f.name).write_text(blob.stdout)
    res = {}
    for label, scripts in (("candidate", None), ("control-7.5", old)):
        c = run.relay(True, scripts=scripts)
        rows = s3_calls(c)
        c.close()
        leaks = [n for n, r in rows if has_marker(r)]
        res[label] = {"leaks": leaks, "refusals": [str(r.get("error"))[:60] for _, r in rows]}
        run.log({"gate": "S3", "route": "proot", "scripts": label, **res[label]})
    ok = not res["candidate"]["leaks"] and bool(res["control-7.5"]["leaks"])
    return {"gate": "S3", "pass": ok, "control_red": bool(res["control-7.5"]["leaks"])}


def loose_object_bytes(kind: str, payload: bytes) -> tuple[str, bytes]:
    raw = f"{kind} {len(payload)}\0".encode() + payload
    return hashlib.sha1(raw).hexdigest(), zlib.compress(raw)


def s4(run: Run) -> dict:
    oid, obj, genuine = fixture_blob(run, "f1.txt")
    _, valid = loose_object_bytes("blob", f"{MARKER2} outside object\n".encode())
    (run.dir / "outside/valid-object").write_bytes(valid)
    nat = run.relay(False)
    expected, _ = nat.call("git_ro", {"cwd": "/fixture", "args": ["cat-file", "-p", oid]})
    out = {}
    for label, other, marker in (("plaintext-secret", str(run.dir / "outside/plain-secret"), MARKER),
                                 ("outside-valid-object(info)", str(run.dir / "outside/valid-object"), MARKER2)):
        started, stop = run.dir / f"race-{label}.started", run.dir / f"race-{label}.stop"
        racer = run.native("race", background=True, timeout=180, path=str(obj), targets=[genuine, other],
                           seconds=150, started=str(started), stop=str(stop))
        t0 = time.monotonic()
        while not started.exists() and time.monotonic() - t0 < 30:
            time.sleep(0.05)
        counts = {"correct": 0, "refused": 0, "git_error": 0, "marker": 0, "other": 0}
        for _ in range(300):
            r, _ = nat.call("git_ro", {"cwd": "/fixture", "args": ["cat-file", "-p", oid]})
            if has_marker(r, marker):
                counts["marker"] += 1
            elif git_view(r) == git_view(expected):
                counts["correct"] += 1
            elif "error" in r:
                counts["refused"] += 1
            elif r.get("returncode"):
                counts["git_error"] += 1
            else:
                counts["other"] += 1
        stop.write_text("1")
        racer.wait(60)
        now = run.native("readlink", paths=[str(obj)])["targets"][str(obj)]
        out[label] = {**counts, "restored": now == genuine, "started": started.exists()}
        run.log({"gate": "S4", "case": label, **out[label]})
    alive = (Path(f"/proc/{int((run.dir / 'r/d.pid').read_text())}")).exists()
    nat.close()
    p = out["plaintext-secret"]
    ok = p["started"] and p["marker"] == 0 and p["other"] == 0 and p["restored"] and alive \
        and out["outside-valid-object(info)"]["restored"]
    return {"gate": "S4", "pass": ok, "daemon_alive": alive}


class FastPeak:
    def __init__(self, roots: list[int]) -> None:
        self.roots, self.peak, self.child_peak, self._stop = roots, 0, 0, threading.Event()
        self.th = threading.Thread(target=self.loop, daemon=True)

    def loop(self) -> None:
        while not self._stop.is_set():
            tot = 0
            for pid in set(descendants(self.roots)) | set(self.roots):
                try:
                    roll = Path(f"/proc/{pid}/smaps_rollup").read_text()
                    pss = int(next(x for x in roll.splitlines() if x.startswith("Pss:")).split()[1])
                except (OSError, StopIteration, ValueError):
                    continue
                tot += pss
                if pid not in self.roots:
                    self.child_peak = max(self.child_peak, pss)
            self.peak = max(self.peak, tot)
            self._stop.wait(0.02)

    def __enter__(self):
        self.th.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self.th.join()


def plant_genuine(run: Run, name: str, data: bytes, oid: str) -> None:
    """Create a genuine PRoot link2symlink object: write tmp_obj_* then link() it in PRoot, like git."""
    tmp = run.dir / "ws/.git/objects" / name
    tmp.write_bytes(data)
    dest = run.dir / "ws/.git/objects" / oid[:2] / oid[2:]
    dest.parent.mkdir(exist_ok=True)
    os.link(tmp, dest)
    tmp.unlink()


def s5(run: Run) -> dict:
    bad_oid = "ab" + "c" * 38
    plant_genuine(run, "tmp_obj_Bad123", b"\x78\x9c this is not zlib", bad_oid)
    bomb_oid, bomb = loose_object_bytes("blob", b"\0" * (64 * 1024 * 1024))
    plant_genuine(run, "tmp_obj_Bmb123", bomb, bomb_oid)
    links = run.native("readlink", paths=[str(run.dir / "ws/.git/objects" / o[:2] / o[2:]) for o in (bad_oid, bomb_oid)])
    shaped = all(t.startswith(L2S + "/.l2s.tmp_obj_") for t in links["targets"].values())
    nat = run.relay(False)
    dpid = int((run.dir / "r/d.pid").read_text())
    rows = {}
    # Amendment A3: git children live < 50 ms; measure them natively at 1 ms, daemon children only.
    kstart, kstop = run.dir / "s5-kids.started", run.dir / "s5-kids.stop"
    nh = run.nhelp + 1
    kids = run.native("pollkids", background=True, timeout=120, pidfile=str(run.dir / "r/d.pid"),
                      started=str(kstart), stop=str(kstop), seconds=90)
    t0 = time.monotonic()
    while not kstart.exists() and time.monotonic() - t0 < 30:
        time.sleep(0.05)
    with FastPeak([dpid, nat.proc.pid]) as fp:
        for label, a in (("corrupt", ["cat-file", "-p", bad_oid]), ("bomb-size", ["cat-file", "-s", bomb_oid]),
                         ("bomb-content", ["cat-file", "-p", bomb_oid]), ("bomb-show", ["show", bomb_oid])):
            r, ms = nat.call("git_ro", {"cwd": "/fixture", "args": a})
            v = git_view(r)
            rows[label] = {"error": v.get("error"), "returncode": v.get("returncode"), "stdout_len": len(v.get("stdout") or ""),
                           "truncated": v.get("truncated"), "ms": round(ms, 1)}
    kstop.write_text("1")
    kids.wait(60)
    kid = json.loads((run.dir / f"helper-{nh}.result.json").read_text())
    alive = Path(f"/proc/{dpid}").exists()
    ping = nat.rpc("ping", {})
    nat.close()
    child = kid["pss_kib"] if kid["seen"] else None  # null, never 0, when no child was observed
    res = {"rows": rows, "l2s_shaped": shaped, "daemon_relay_peak_pss_kib": fp.peak, "child_poll": kid,
           "child_peak_pss_kib": child, "group_peak_pss_kib": None if child is None else fp.peak + child,
           "daemon_alive": alive, "ping": "result" in ping}
    run.log({"gate": "S5", **res})
    bounded = all((r["error"] or r["returncode"] not in (0, None) or r["stdout_len"] <= 2 * 1024 * 1024)
                  for k, r in rows.items() if k != "bomb-size")
    if child is None:
        return {"gate": "S5", "pass": None, "verdict": "INVALID", "reason": "no git child observed"}
    ok = shaped and alive and res["ping"] and bounded and res["group_peak_pss_kib"] <= 256 * 1024 \
        and rows["bomb-size"]["returncode"] == 0
    return {"gate": "S5", "pass": ok, "group_peak_pss_kib": res["group_peak_pss_kib"]}


def s6(run: Run) -> dict:
    r6, b6 = run.dir / "r6", str(run.dir / "budget6")
    r6.mkdir()
    call = ("git_ro", {"cwd": "/root/projects/GPU加速/src/f8-proot-fast", "args": ["log", "-n", "3", "--oneline"]})
    def one(extra=("--auto-start",)) -> tuple[dict, str]:
        c = run.relay(False, extra=list(extra), bdir=b6, sock=r6 / "m.sock")
        r, _ = c.call(*call)
        _, err = c.close()
        return git_view(r), err
    res = {}
    first, err1 = one()
    pid1 = int((r6 / "d.pid").read_text()) if (r6 / "d.pid").exists() else None
    env1 = Path(f"/proc/{pid1}/environ").read_bytes().split(b"\0") if pid1 else []
    status1 = Path(f"/proc/{pid1}/status").read_text() if pid1 else ""
    try:
        fd, _ = budget.acquire_lease(b6, daemon=True)
        os.close(fd)
        lease_held = False
    except (OSError, ValueError):
        lease_held = True
    start_ev = [json.loads(x) for x in (r6 / "audit.jsonl").read_text().splitlines() if '"action": "start"' in x] if (r6 / "audit.jsonl").exists() else []
    res["a"] = {"pid": pid1, "result_ok": first.get("returncode") == 0, "budget_env": f"F8_HYBRID2_BUDGET_DIR={b6}".encode() in env1,
                "tracer0": "TracerPid:\t0" in status1, "lease_held": lease_held,
                "start": start_ev[-1] if start_ev else None, "stderr": err1}
    stop = sh([sys.executable, "-B", str(run.dir / "scripts/f8_hybrid2_ctl.py"), "--dir", str(r6), "stop"], timeout=30)
    second, err2 = one()
    pid2 = int((r6 / "d.pid").read_text()) if (r6 / "d.pid").exists() else None
    res["b"] = {"stop": stop.stdout.strip()[-200:], "pid2": pid2, "relaunched": bool(pid2 and pid2 != pid1),
                "same_result": second == first, "stderr": err2}
    dis = sh([sys.executable, "-B", str(run.dir / "scripts/f8_hybrid2_ctl.py"), "--dir", str(r6), "disable"], timeout=30)
    third, err3 = one()
    res["c"] = {"disable": dis.stdout.strip()[-200:], "fallback": "fallback=proot" in err3, "same_result": third == first}
    run.log({"gate": "S6", **res})
    a = res["a"]
    ok = a["result_ok"] and a["budget_env"] and a["tracer0"] and a["lease_held"] and bool(a["start"]) \
        and a["start"].get("governed") is True and a["start"].get("max_clients") == 4 \
        and res["b"]["relaunched"] and res["b"]["same_result"] and res["c"]["fallback"] and res["c"]["same_result"]
    return {"gate": "S6", "pass": ok}


def s7(run: Run) -> dict:
    nat, fb = run.relay(False), run.relay(True)
    out = {}
    for repo in ("/root/projects/GPU加速/src/f8-proot-fast", "/root/projects/GPU加速/src/upstream"):
        links = sh(["find", f"{repo}/.git/objects", "-type", "l"]).stdout.split()
        loose = [p for p in links if len(Path(p).name) == 38]
        oid = Path(loose[0]).parent.name + Path(loose[0]).name
        for label, a in (("log20stat", ["log", "-n", "20", "--stat"]), ("catfile", ["cat-file", "-p", oid])):
            tn = [nat.call("git_ro", {"cwd": repo, "args": a})[1] for _ in range(20)]
            tf = [fb.call("git_ro", {"cwd": repo, "args": a})[1] for _ in range(20)]
            out[f"{repo.rsplit('/', 1)[1]}:{label}"] = {"native_p50": pct(tn, 50), "native_p95": pct(tn, 95),
                                                        "proot_p50": pct(tf, 50), "proot_p95": pct(tf, 95)}
    nat.close(); fb.close()
    scan = run.native("policy_scan", timeout=120, scripts=str(run.dir / "scripts"), roots=run.roots,
                      host_projects=ROOTFS + "/root/projects", home=str(run.dir / "h"), tmp=str(run.dir / "r"),
                      repos=["/root/projects/GPU加速/src/upstream", "/root/projects/GPU加速/src/f8-proot-fast"])
    run.log({"gate": "S7", "latency_ms": out, "native_policy_scan_ms": scan["scan_ms"]})
    return {"gate": "S7", "pass": None, "informational": True}


def redlines() -> dict:
    out = {"x1_inode": sh(["stat", "-c", "%i", "/data/data/com.termux/files/usr/tmp/.X11-unix/X1"]).stdout.strip(),
           "fast9": sh(["bash", "-c", "cd /data/data/com.termux/files/home/build/proot-fast/out8 && sha256sum -c --quiet deployed.sha256 && echo ok"]).stdout.strip(),
           "pilot_scripts": sh(["bash", "-c", f"cd {PILOT} && sha256sum -c --quiet DEPLOYED.sha256 && echo ok"]).stdout.strip(),
           "claude_json": hashlib.sha256(Path("/root/.claude.json").read_bytes()).hexdigest()[:16]}
    pid = Path("/data/data/com.termux/files/home/.f8hyb2/d.pid")
    out["pilot_pid"] = pid.read_text().strip() if pid.exists() else None
    out["pilot_alive"] = bool(out["pilot_pid"]) and Path(f"/proc/{out['pilot_pid']}").exists()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("parent")
    ap.add_argument("--only", default="S1,S2,S3,S4,S5,S6,S7")
    args = ap.parse_args()
    run = Run(Path(args.parent))
    print(f"run={run.dir}", flush=True)
    before = redlines()
    run.log({"event": "redlines-start", **before})
    run.prepare()
    run.log({"event": "prepared", "candidate": (run.dir / "candidate").read_text().strip(),
             "dirty": (run.dir / "candidate.dirty").read_text().strip(),
             "fixture_l2s_links": int((run.dir / "fixture-l2s-links").read_text())})
    gates = {}
    try:
        run.log({"event": "daemon", "pid": run.start_daemon()})
        for name in args.only.split(","):
            try:
                gates[name] = globals()[name.lower()](run)
            except Exception as exc:  # recorded, never silently retried
                gates[name] = {"gate": name, "pass": False, "exception": repr(exc)[:300]}
            run.log({"event": "gate", **gates[name]})
    finally:
        run.stop_daemon()
        sh([sys.executable, "-B", str(run.dir / "scripts/f8_hybrid2_ctl.py"), "--dir", str(run.dir / "r6"), "stop"], timeout=30)
        after = redlines()
        run.log({"event": "redlines-end", **after, "unchanged": {k: before[k] == after[k] for k in before}})
    (run.dir / "s76-judge.json").write_text(json.dumps({"gates": gates, "redlines_unchanged": before == after,
                                                        "candidate": (run.dir / "candidate").read_text().strip()}, indent=1))
    print(json.dumps({k: v.get("pass") for k, v in gates.items()}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
