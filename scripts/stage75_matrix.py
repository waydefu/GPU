#!/usr/bin/env python3
"""Stage 7.5 tiered governance device matrix.

Runs inside PRoot. Relays are PRoot processes; the daemon is started natively
through termux-bg-run with the run directory's ``run-daemon`` script. Every
cell checks its own results and the chain stops at the first failure. See
docs/F8-HYBRID2-STAGE75-TIERED-FREEZE-20261128.md for the frozen cells/gates.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import math
import os
import select
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import f8_hybrid2_budget as budget  # noqa: E402

RUNNER = "/usr/local/bin/termux-bg-run"
CLK = os.sysconf("SC_CLK_TCK")
CEIL = {"pss_kib": 256 * 1024, "threads": 64, "fds": 192}
NORMAL = [
    ("repo_tree_scan", {"root": "/fixture/small"}),
    ("repo_text_search", {"root": "/fixture/sample.txt", "pattern": "needle", "fixed_string": True}),
    ("git_ro", {"cwd": "/fixture", "args": ["status", "--short"]}),
    ("python_json_summary", {"path": "/fixture/sample.jsonl"}),
]
HEAVY = [
    ("repo_tree_scan", {"root": "/fixture/tree", "max_entries": 50000}),
    ("repo_text_search", {"root": "/fixture/corpus.txt", "pattern": "needle", "fixed_string": True, "max_matches": 5000}),
    ("git_ro", {"cwd": "/fixture", "args": ["show", "HEAD", "--", "corpus.txt"]}),
    ("python_json_summary", {"path": "/fixture/sample.jsonl"}),
]
NATIVE = {"repo_tree_scan", "repo_text_search", "git_ro"}
BIG_PING_PAD = 500_000


def call(i: int, name: str, args: dict) -> dict:
    return {"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": name, "arguments": args}}


class Client:
    """Relay process with an unbuffered, deadline-bounded line reader."""

    def __init__(self, proc: subprocess.Popen) -> None:
        self.p = proc
        self.buf = bytearray()

    def send(self, obj: dict | bytes) -> None:
        data = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
        self.p.stdin.write(data + b"\n")
        self.p.stdin.flush()

    def recv(self, timeout: float = 60.0) -> dict:
        deadline = time.monotonic() + timeout
        fd = self.p.stdout.fileno()
        while b"\n" not in self.buf:
            left = deadline - time.monotonic()
            if left <= 0 or not select.select([fd], [], [], left)[0]:
                raise TimeoutError("relay reply timeout")
            chunk = os.read(fd, 1 << 20)
            if not chunk:
                raise EOFError(self.p.stderr.read().decode(errors="replace")[-500:])
            self.buf.extend(chunk)
        nl = self.buf.index(b"\n")
        line = bytes(self.buf[:nl])
        del self.buf[: nl + 1]
        return json.loads(line)

    def quiet(self, seconds: float) -> bool:
        return b"\n" not in self.buf and not select.select([self.p.stdout.fileno()], [], [], seconds)[0]

    def init(self) -> None:
        self.send({"jsonrpc": "2.0", "id": "init", "method": "initialize", "params": {"protocolVersion": "2025-03-26"}})
        assert "result" in self.recv(), "initialize failed"
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def close(self, expect_rc: int | None = 0, timeout: float = 30.0) -> int:
        if self.p.stdin and not self.p.stdin.closed:
            self.p.stdin.close()
        rc = self.p.wait(timeout=timeout)
        for s in (self.p.stdout, self.p.stderr):
            s.close()
        if expect_rc is not None:
            assert rc == expect_rc, f"relay rc={rc}"
        return rc

    def kill(self) -> None:
        if self.p.poll() is None:
            self.p.kill()
        self.p.wait()
        for s in (self.p.stdin, self.p.stdout, self.p.stderr):
            if s and not s.closed:
                s.close()


def descendants(roots: list[int]) -> list[int]:
    """Roots plus every descendant, from a PPID scan of /proc/*/stat.

    This kernel has no /proc/PID/task/TID/children (CONFIG_PROC_CHILDREN off),
    so walking those files silently finds no child at all.
    """
    kids: dict[int, list[int]] = {}
    for d in os.listdir("/proc"):
        if d.isdigit():
            try:
                ppid = int(Path(f"/proc/{d}/stat").read_text().rsplit(")", 1)[1].split()[1])
            except (OSError, ValueError, IndexError):
                continue
            kids.setdefault(ppid, []).append(int(d))
    out, todo = [], [r for r in roots if r > 0]
    while todo:
        pid = todo.pop()
        if pid in out:
            continue
        out.append(pid)
        todo.extend(kids.get(pid, []))
    return out


def proc_status(pid: int) -> dict[str, str]:
    return dict(x.split(":", 1) for x in Path(f"/proc/{pid}/status").read_text().splitlines() if ":" in x)


class Sampler:
    """0.2 s group snapshots: totals, per-child peak, CPU ticks, host stop gate."""

    def __init__(self, roots_fn) -> None:
        self.roots_fn = roots_fn
        self.peak: dict[str, int] = {}
        self.samples = 0
        self.restricted = 0
        self.child_peak_pss = 0
        self.ticks: dict[int, int] = {}
        self.temps: list[tuple[float, int, int, int]] = []
        self.stop_reason: str | None = None
        self._stop = threading.Event()
        self._th = threading.Thread(target=self._loop, daemon=True)
        zones = {p.parent: p.read_text().strip() for p in Path("/sys/class/thermal").glob("thermal_zone*/type")}
        self.cpu_zones = [p / "temp" for p, n in zones.items() if n.startswith(("cpu-0-", "cpu-1-"))]
        self.batt_zones = [p / "temp" for p, n in zones.items() if n == "battery"]

    def host(self) -> tuple[int, int, int]:
        avail = int(next(r.split()[1] for r in Path("/proc/meminfo").read_text().splitlines() if r.startswith("MemAvailable:")))
        cpu = max(int(p.read_text()) for p in self.cpu_zones)
        batt = max(int(p.read_text()) for p in self.batt_zones)
        return avail, cpu, batt

    def snapshot(self, roots: list[int]) -> dict[str, int]:
        todo, seen = descendants(roots), set()
        tot = dict.fromkeys(("pss_kib", "rss_kib", "threads", "fds", "swap_pss_kib", "private_dirty_kib",
                             "rss_anon_kib", "rss_file_kib", "restricted"), 0)
        while todo:
            pid = todo.pop()
            if pid in seen:
                continue
            seen.add(pid)
            proc = Path(f"/proc/{pid}")
            try:
                roll = dict(r.split(":", 1) for r in (proc / "smaps_rollup").read_text().splitlines() if ":" in r)
                st = proc_status(pid)
                pss = int(roll["Pss"].split()[0])
                tot["pss_kib"] += pss
                tot["swap_pss_kib"] += int(roll["SwapPss"].split()[0])
                tot["private_dirty_kib"] += int(roll["Private_Dirty"].split()[0])
                tot["rss_kib"] += int(st["VmRSS"].split()[0])
                tot["rss_anon_kib"] += int(st["RssAnon"].split()[0])
                tot["rss_file_kib"] += int(st["RssFile"].split()[0])
                tot["threads"] += int(st["Threads"])
                tot["fds"] += len(list((proc / "fd").iterdir()))
                if pid not in roots:
                    self.child_peak_pss = max(self.child_peak_pss, pss)
                stat = (proc / "stat").read_text().rsplit(")", 1)[1].split()
                self.ticks[pid] = max(self.ticks.get(pid, 0), int(stat[11]) + int(stat[12]))
            except PermissionError:
                tot["restricted"] += 1
            except (FileNotFoundError, ProcessLookupError, KeyError, ValueError):
                pass
        return tot

    def _loop(self) -> None:
        while not self._stop.is_set():
            snap = self.snapshot(self.roots_fn())
            self.samples += 1
            self.restricted += int(snap["restricted"] > 0)
            self.peak = {k: max(self.peak.get(k, 0), v) for k, v in snap.items()}
            avail, cpu, batt = self.host()
            self.temps.append((time.monotonic(), cpu, batt, avail))
            if avail < 1536 * 1024 or cpu > 85000 or batt > 42000:
                self.stop_reason = f"host-stop avail={avail} cpu={cpu} batt={batt}"
            self._stop.wait(0.2)

    def __enter__(self) -> "Sampler":
        self._th.start()
        return self

    def __exit__(self, *exc) -> None:
        self._stop.set()
        self._th.join()

    def summary(self) -> dict:
        over = {k: self.peak.get(k, 0) for k in CEIL if self.peak.get(k, 0) > CEIL[k]}
        return {"peak": self.peak, "samples": self.samples, "restricted_samples": self.restricted,
                "child_peak_pss_kib": self.child_peak_pss, "over_ceiling": over,
                "max_cpu_millic": max((t[1] for t in self.temps), default=None),
                "max_battery_millic": max((t[2] for t in self.temps), default=None),
                "min_memavailable_kib": min((t[3] for t in self.temps), default=None),
                "host_stop": self.stop_reason}


def pct(values: list[float], p: int) -> float:
    s = sorted(values)
    return round(s[max(0, math.ceil(len(s) * p / 100) - 1)], 2)


class Matrix:
    def __init__(self, run: Path, mode: int) -> None:
        self.dir, self.mode = run, mode
        self.sock = run / "r/m.sock"
        self.ready = run / "r/ready"
        self.bdir = str(run / "budget")
        base = {k: v for k, v in os.environ.items() if k not in ("F8_NO_HYBRID", "F8_HYBRID2_BUDGET_DIR")}
        base["F8_HYBRID2_TRUSTED_GIT_ROOTS"] = '["/fixture"]'
        self.env = {**base, "F8_HYBRID2_BUDGET_DIR": self.bdir}
        self.oracle_env = {**base, "F8_NO_HYBRID": "1"}
        self.prof = budget.PROFILES[mode]
        self.daemon = 0
        self.runner: subprocess.Popen | None = None
        self.starts = 0
        self.idle: dict = {}
        self.oracle_cache: dict[str, dict] = {}
        self.relays: list[Client] = []
        self.out = open(run / f"matrix-{mode}.jsonl", "a")

    def log(self, obj: dict) -> None:
        line = json.dumps(obj, sort_keys=True)
        print(line, flush=True)
        self.out.write(line + "\n")
        self.out.flush()

    # daemon lifecycle ------------------------------------------------------
    def start_daemon(self) -> None:
        self.starts += 1
        prev = self.daemon
        log = open(self.dir / f"runner-{self.starts}.log", "wb")
        self.runner = subprocess.Popen([RUNNER, "--timeout", "7200", "--log-file", str(self.dir / f"daemon-{self.starts}.log"),
                                        "--tail", "20", str(self.dir / "run-daemon")], stdout=log, stderr=log)
        log.close()
        for _ in range(300):
            try:
                ready = json.loads(self.ready.read_text())
                if ready["pid"] != prev and self.sock.exists():
                    break
            except (OSError, ValueError, KeyError):
                pass
            assert self.runner.poll() is None, "daemon runner exited early"
            time.sleep(0.1)
        else:
            raise RuntimeError("daemon not ready")
        assert ready["tracer_pid"] == 0
        assert str(HERE / "f8_hybrid2_daemon.py").encode() in Path(f"/proc/{ready['pid']}/cmdline").read_bytes().split(b"\0")
        self.daemon = ready["pid"]

    def stop_daemon(self) -> None:
        assert str(HERE / "f8_hybrid2_daemon.py").encode() in Path(f"/proc/{self.daemon}/cmdline").read_bytes().split(b"\0")
        os.kill(self.daemon, signal.SIGTERM)
        self.runner.wait(timeout=90)
        for name in ("m.sock", "d.pid", "ready"):
            assert not (self.dir / "r" / name).exists(), name

    # relays ----------------------------------------------------------------
    def spawn(self, *, fallback: bool = False, tag: str = "main", env: dict | None = None) -> Client:
        argv = [sys.executable, "-B", str(HERE / "f8_hybrid2_relay.py"), "--socket", str(self.sock),
                "--map", f"/fixture={self.dir}/ws2", "--git-bin", "/usr/bin/git",
                "--route-log", str(self.dir / f"routes-{self.mode}-{tag}.jsonl")]
        if not fallback:
            argv.append("--no-fallback")
        p = subprocess.Popen(argv, env=env or self.env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return Client(p)

    def roots(self) -> list[int]:
        return [self.daemon] + [c.p.pid for c in self.relays if c.p.poll() is None]

    def expect(self, name: str, args: dict) -> dict:
        key = json.dumps([name, args], sort_keys=True)
        if key not in self.oracle_cache:
            c = self.spawn(fallback=True, tag="oracle", env=self.oracle_env)
            try:
                c.init()
                c.send(call(1, name, args))
                self.oracle_cache[key] = c.recv(300)
            finally:
                c.close()
        return self.oracle_cache[key]

    def check(self, resp: dict, name: str, args: dict) -> None:
        want = self.expect(name, args)
        assert resp.get("result") == want.get("result") and resp.get("error") == want.get("error"), \
            f"oracle mismatch {name}: {str(resp)[:300]}"
        if "result" in resp:
            assert not resp["result"].get("isError"), str(resp)[:300]

    def daemon_counts(self) -> tuple[int, int]:
        st = proc_status(self.daemon)
        return int(st["Threads"]), len(list(Path(f"/proc/{self.daemon}/fd").iterdir()))

    def settle(self, sampler: Sampler) -> dict:
        time.sleep(3)
        rows = []
        for i in range(3):
            rows.append(sampler.snapshot([self.daemon]))
            if i < 2:
                time.sleep(1)
        return {k: median(r[k] for r in rows) for k in rows[0]}

    def drain(self) -> dict:
        for c in self.relays:
            if c.p.poll() is None:
                c.kill()
        self.relays = []
        for _ in range(750):
            if self.daemon_counts() == (self.idle["threads"], self.idle["fds"]):
                break
            time.sleep(0.02)
        else:
            raise AssertionError(f"daemon not drained: {self.daemon_counts()} vs {self.idle['threads'], self.idle['fds']}")
        leases = [budget.acquire_lease(self.bdir)[0] for _ in range(self.mode)]
        pool = budget.ExecPool(self.bdir, self.prof.exec_slots)
        execs = [pool.try_acquire() for _ in range(self.prof.exec_slots)]
        try:
            assert all(fd is not None for fd in execs), "exec slot still held"
        finally:
            for fd in leases + [e for e in execs if e is not None]:
                os.close(fd)
        return {"daemon_threads_fds": self.daemon_counts(), "leases_free": self.mode, "exec_free": self.prof.exec_slots}

    def hold_exec(self) -> list[int]:
        pool = budget.ExecPool(self.bdir, self.prof.exec_slots)
        held = []
        deadline = time.monotonic() + 30
        while len(held) < self.prof.exec_slots:
            fd = pool.try_acquire()
            if fd is not None:
                held.append(fd)
            assert time.monotonic() < deadline, "exec slots not free"
            time.sleep(0.01)
        return held

    def start_relays(self, n: int, **kw) -> list[Client]:
        cs = [self.spawn(**kw) for _ in range(n)]
        self.relays.extend(cs)
        for c in cs:
            c.init()
        return cs

    def daemon_ticks(self) -> int:
        stat = Path(f"/proc/{self.daemon}/stat").read_text().rsplit(")", 1)[1].split()
        return int(stat[11]) + int(stat[12])

    def cool(self, limit: int = 65000, max_wait: float = 600) -> int:
        """Start every cell from a comparable temperature (amendment A2); returns the start reading."""
        probe = Sampler(self.roots)
        deadline = time.monotonic() + max_wait
        while True:
            cpu = probe.host()[1]
            if cpu <= limit or time.monotonic() > deadline:
                return cpu
            time.sleep(5)

    def cell(self, name: str, fn, *, attempt: int = 1) -> dict:
        start_cpu = self.cool()
        t0 = time.monotonic()
        dpid, d0 = self.daemon, self.daemon_ticks()
        with Sampler(self.roots) as smp:
            extra = fn(smp) or {}
        res = {"cell": name, "mode": self.mode, "attempt": attempt, "start_cpu_millic": start_cpu,
               "wall_s": round(time.monotonic() - t0, 2), **smp.summary(), **extra}
        res["daemon_cpu_s"] = round((self.daemon_ticks() - d0) / CLK, 2) if self.daemon == dpid else None
        res["relay_cpu_s"] = round(sum(v for k, v in smp.ticks.items() if k != self.daemon) / CLK, 2)
        if "ops" in res and res.get("latencies_ms"):
            lat = res.pop("latencies_ms")
            res.update(p50_ms=pct(lat, 50), p95_ms=pct(lat, 95), p99_ms=pct(lat, 99),
                       throughput_per_s=round(res["ops"] / res["wall_s"], 2))
        res["G2"] = "PASS" if not res["over_ceiling"] else "FAIL"
        if smp.stop_reason:
            res["G2"] = "INVALID"
        res["drain"] = self.drain()
        self.log(res)
        if res["G2"] == "INVALID" and attempt == 1:
            return self.cell(name, fn, attempt=2)  # A2: one recorded rerun after cooling
        assert res["G2"] == "PASS", res["G2"]
        return res

    # cells -----------------------------------------------------------------
    def warm(self) -> None:
        c = self.spawn(tag="warm")
        c.init()
        for i in range(48):
            name, args = NORMAL[i % 4]
            c.send(call(i, name, args))
            self.check(c.recv(), name, args)
        for name, args in HEAVY:
            self.expect(name, args)
        c.close()
        with Sampler(self.roots) as smp:
            idle = self.settle(smp)
        self.idle = idle
        self.log({"event": "idle", "mode": self.mode, "daemon_pid": self.daemon, "idle": idle})

    def c1(self, cycle: int) -> dict:
        ops = self.mode * math.ceil(1000 / self.mode)

        def body(smp: Sampler) -> dict:
            cs = self.start_relays(self.mode)
            idle_rows = []
            for _ in range(3):
                pids = [c.p.pid for c in cs]
                idle_rows.append(sum(smp.snapshot([p])["pss_kib"] for p in pids) / len(pids))
                time.sleep(0.5)
            barrier = threading.Barrier(self.mode)

            def run(c: Client) -> list[float]:
                lat = []
                per = ops // self.mode
                barrier.wait(timeout=10)
                start = time.monotonic()
                for n in range(per):
                    time.sleep(max(0, start + n * 60 / per - time.monotonic()))
                    name, args = NORMAL[n % 4]
                    t = time.monotonic()
                    c.send(call(n + 10, name, args))
                    r = c.recv()
                    lat.append((time.monotonic() - t) * 1000)
                    assert r["id"] == n + 10
                    self.check(r, name, args)
                time.sleep(max(0, start + 60 - time.monotonic()))
                return lat

            with cf.ThreadPoolExecutor(self.mode) as ex:
                lats = [x for f in [ex.submit(run, c) for c in cs] for x in f.result()]
            for c in cs:
                c.close()
            self.relays = []
            settled = self.settle(smp)
            drift = 100.0 * (settled["rss_kib"] - self.idle["rss_kib"]) / self.idle["rss_kib"]
            idle_ret = self.idle["pss_kib"] + self.idle["swap_pss_kib"]
            ret = settled["pss_kib"] + settled["swap_pss_kib"]
            return {"ops": len(lats), "latencies_ms": lats, "cycle": cycle, "relay_idle_pss_kib": median(idle_rows),
                    "settled_daemon": settled, "rss_drift_pct": round(drift, 2),
                    "G4": "PASS" if abs(drift) <= 10 else "FAIL", "retained_kib": ret, "idle_retained_kib": idle_ret}
        return self.cell(f"C1-normal-{cycle}", body)

    def c2(self) -> dict:
        def body(_smp: Sampler) -> dict:
            cs = self.start_relays(self.mode)
            ping = {"jsonrpc": "2.0", "id": 0, "method": "ping", "params": {"pad": "a" * BIG_PING_PAD}}
            raw = json.dumps(ping).encode()
            assert len(raw) < budget.GOVERNED.request_frame and budget.parse_cost(raw) < budget.GOVERNED.parse_budget

            def run(c: Client) -> list[float]:
                lat = []
                for rnd in range(12):
                    t = time.monotonic()
                    c.send(raw)
                    assert c.recv(120) == {"jsonrpc": "2.0", "id": 0, "result": {}}
                    lat.append((time.monotonic() - t) * 1000)
                    for k, (name, args) in enumerate(HEAVY):
                        t = time.monotonic()
                        c.send(call(rnd * 10 + k + 1, name, args))
                        r = c.recv(300)
                        lat.append((time.monotonic() - t) * 1000)
                        self.check(r, name, args)
                    time.sleep(1.5)  # A2 pacing: payload size is the subject, not duty cycle
                return lat

            with cf.ThreadPoolExecutor(self.mode) as ex:
                lats = [x for f in [ex.submit(run, c) for c in cs] for x in f.result()]
            for c in cs:
                c.close()
            self.relays = []
            return {"ops": len(lats), "latencies_ms": lats, "ping_frame_bytes": len(raw), "ping_parse_cost": budget.parse_cost(raw)}
        return self.cell("C2-maxload", body)

    def c3(self) -> dict:
        def body(_smp: Sampler) -> dict:
            cs = self.start_relays(self.mode)
            extra = self.spawn(tag="extra")
            rc = extra.p.wait(timeout=20)
            err = extra.p.stderr.read()
            extra.kill()
            assert rc == 3 and b"budget exhausted" in err, (rc, err[-200:])
            d2 = subprocess.run([sys.executable, "-B", str(HERE / "f8_hybrid2_daemon.py"), "--socket", str(self.dir / "r/o.sock"),
                                 "--pidfile", str(self.dir / "r/o.pid"), "--home", str(self.dir / "h"), "--tmp", str(self.dir / "r"),
                                 "--skip-tracer-check"], env=self.env, capture_output=True, timeout=20)
            assert d2.returncode == 3 and b"budget exhausted" in d2.stderr, d2
            cs[0].close()
            self.relays.remove(cs[0])
            again = self.start_relays(1)[0]
            name, args = NORMAL[0]
            again.send(call(5, name, args))
            self.check(again.recv(), name, args)
            for c in list(self.relays):
                c.close()
            self.relays = []
            return {"extra_relay_rc": rc, "second_daemon_rc": d2.returncode, "slot_reuse": "PASS"}
        return self.cell("C3-overload", body)

    def c4(self) -> dict:
        def body(_smp: Sampler) -> dict:
            cs = self.start_relays(self.mode)
            for c in cs:
                for k, (name, args) in enumerate(HEAVY):
                    c.send(call(100 + k, name, args))
            time.sleep(5)
            for c in cs:
                got = {}
                for _ in HEAVY:
                    r = c.recv(300)
                    got[r["id"]] = r
                for k, (name, args) in enumerate(HEAVY):
                    self.check(got[100 + k], name, args)
            for c in cs:
                c.close()
            self.relays = []
            return {"ops": self.mode * len(HEAVY)}
        return self.cell("C4-slowread", body)

    def c5(self) -> dict:
        def body(_smp: Sampler) -> dict:
            cs = self.start_relays(self.mode)
            tree = HEAVY[0]
            for i, c in enumerate(cs):
                held = self.hold_exec()
                try:
                    c.send(call(1, *tree))
                    time.sleep(0.2)
                    c.send({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 1}})
                    time.sleep(0.2)
                finally:
                    for fd in held:
                        os.close(fd)
                c.send({"jsonrpc": "2.0", "id": 2, "method": "ping"})
                assert c.recv(30)["id"] == 2
                assert c.quiet(1.0), "cancelled request answered"
                c.send(call(3, tree[0], {**tree[1], "timeout_s": 0.001}))
                assert c.recv(60)["error"] == {"code": -32001, "message": "Tool 'repo_tree_scan' timed out"}
            for c in cs[1:]:
                for k, (name, args) in enumerate(NORMAL):
                    c.send(call(10 + k, name, args))
                c.p.stdin.close()
                got = {r["id"]: r for r in (c.recv(120) for _ in NORMAL)}
                for k, (name, args) in enumerate(NORMAL):
                    self.check(got[10 + k], name, args)
                c.close()
            victim = cs[0]
            victim.send(call(20, *tree))
            time.sleep(0.05)
            victim.kill()
            self.relays = []
            return {"cancel": "PASS", "timeout": "PASS", "halfclose": self.mode - 1, "killed_relay": victim.p.pid}
        return self.cell("C5-lifecycle", body)

    def c6(self) -> dict:
        def body(_smp: Sampler) -> dict:
            cs = self.start_relays(self.mode)
            held = self.hold_exec()
            try:
                for c in cs:
                    c.send(call(1, *NORMAL[0]))
                time.sleep(0.5)
                self.stop_daemon()
            finally:
                for fd in held:
                    os.close(fd)
            for c in cs:
                r = c.recv(30)
                assert r["id"] == 1 and r["error"]["code"] == -32000 and "disconnected" in r["error"]["message"], r
                c.send(call(2, *NORMAL[0]))
                assert c.recv(30)["error"]["message"] == "Native daemon disconnected"
                c.send(call(3, *NORMAL[3]))
                self.check(c.recv(60), *NORMAL[3])
                c.close()
            self.relays = []
            daemon_down = self.daemon
            self.daemon = 0
            fb = self.start_relays(self.mode, fallback=True, tag="fallback")
            extra = self.spawn(fallback=True, tag="extra")
            assert extra.p.wait(timeout=20) == 3
            extra.kill()
            for c in fb:
                for k, (name, args) in enumerate(NORMAL):
                    c.send(call(k, name, args))
                    self.check(c.recv(120), name, args)
                c.close()
            self.relays = []
            self.start_daemon()
            self.warm()
            ns = self.start_relays(self.mode, tag="restart")
            for c in ns:
                for k, (name, args) in enumerate(NORMAL):
                    c.send(call(k, name, args))
                    self.check(c.recv(120), name, args)
                c.close()
            self.relays = []
            routes = [json.loads(x) for x in (self.dir / f"routes-{self.mode}-restart.jsonl").read_text().splitlines()]
            assert all((r["target"] == "native_uds") == (r["tool"] in NATIVE) for r in routes) and routes
            return {"stopped_daemon": daemon_down, "restarted_daemon": self.daemon, "fallback_relays": self.mode}
        return self.cell("C6-restart-fallback", body)

    def soak(self, seconds: int) -> dict:
        def body(smp: Sampler) -> dict:
            cs = self.start_relays(self.mode, tag="soak")
            rate = 1000 / 60

            def run(c: Client) -> list[float]:
                lat = []
                per = int(seconds * rate / self.mode)
                start = time.monotonic()
                for n in range(per):
                    time.sleep(max(0, start + n * seconds / per - time.monotonic()))
                    name, args = NORMAL[n % 4]
                    t = time.monotonic()
                    c.send(call(n + 10, name, args))
                    self.check(c.recv(), name, args)
                    lat.append((time.monotonic() - t) * 1000)
                return lat

            with cf.ThreadPoolExecutor(self.mode) as ex:
                lats = [x for f in [ex.submit(run, c) for c in cs] for x in f.result()]
            for c in cs:
                c.close()
            self.relays = []
            end = smp.temps[-1][0]
            windows = [median(t[1] for t in smp.temps if end - 20 * (k + 1) < t[0] <= end - 20 * k) for k in (2, 1, 0)]
            settled = self.settle(smp)
            drift = 100.0 * (settled["rss_kib"] - self.idle["rss_kib"]) / self.idle["rss_kib"]
            return {"ops": len(lats), "latencies_ms": lats, "thermal_windows_millic": windows,
                    "thermal": "PASS" if max(windows) - min(windows) <= 2000 else "FAIL",
                    "rss_drift_pct": round(drift, 2), "settled_daemon": settled}
        return self.cell("SOAK", body)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--mode", type=int, required=True, choices=sorted(budget.PROFILES))
    ap.add_argument("--cells", default="C1,C2,C3,C4,C5,C6")
    ap.add_argument("--soak", type=int, default=0)
    ap.add_argument("--cycles", type=int, default=3)
    args = ap.parse_args()
    m = Matrix(Path(args.run).resolve(), args.mode)
    cells = args.cells.split(",")
    m.log({"event": "start", "mode": args.mode, "profile": budget.PROFILES[args.mode].__dict__, "cells": cells,
           "limits": budget.GOVERNED.__dict__})
    m.start_daemon()
    try:
        m.warm()
        for name in cells:
            if name == "C1":
                for k in range(1, args.cycles + 1):
                    m.c1(k)
            else:
                getattr(m, name.lower())()
        if args.soak:
            m.soak(args.soak)
        bad = []
        for log in m.dir.glob(f"routes-{args.mode}-*.jsonl"):
            if log.name.endswith(("-oracle.jsonl", "-fallback.jsonl")):
                continue
            bad += [r for r in map(json.loads, log.read_text().splitlines()) if (r["target"] == "native_uds") != (r["tool"] in NATIVE)]
        assert not bad, bad[:3]
        m.log({"event": "done", "mode": args.mode, "result": "PASS", "route_audit": "PASS"})
        return 0
    except BaseException as exc:
        m.log({"event": "abort", "mode": args.mode, "error": f"{type(exc).__name__}: {exc}"[:2000]})
        raise
    finally:
        for c in m.relays:
            c.kill()
        if m.daemon:
            try:
                m.stop_daemon()
            except Exception as exc:  # noqa: BLE001
                m.log({"event": "stop-failed", "error": str(exc)})


if __name__ == "__main__":
    raise SystemExit(main())
