#!/usr/bin/env python3
"""Stage 7.6 amendment A4: wait for a thermally settled, idle device before a judged matrix run.

Settled = battery <= 38.0 C, hottest CPU sensor <= 50.0 C, and the medians of three consecutive
60 s windows (1 s samples of the hottest CPU sensor) within 1.0 C. Gives up after 120 min.
Usage: stage76_thermal_settle.py OUT_JSON   (exit 0 settled, 3 not settled)
"""
import json, sys, time
from pathlib import Path
from statistics import median

zones = {p.parent: p.read_text().strip() for p in Path("/sys/class/thermal").glob("thermal_zone*/type")}
cpu = [p / "temp" for p, n in zones.items() if n.startswith(("cpu-0-", "cpu-1-"))]
batt = [p / "temp" for p, n in zones.items() if n == "battery"]
read = lambda ps: max(int(p.read_text()) for p in ps)
deadline, windows, log = time.monotonic() + 7200, [], []
t0 = time.time()
while time.monotonic() < deadline:
    samples = []
    for _ in range(60):
        samples.append(read(cpu)); time.sleep(1)
    w = {"t": round(time.time() - t0), "cpu_median": median(samples), "cpu_max": max(samples), "battery": read(batt)}
    windows.append(w); log.append(w)
    last = windows[-3:]
    ok = (len(last) == 3 and max(x["cpu_median"] for x in last) - min(x["cpu_median"] for x in last) <= 1000
          and last[-1]["battery"] <= 38000 and last[-1]["cpu_max"] <= 50000)
    if ok:
        Path(sys.argv[1]).write_text(json.dumps({"settled": True, "windows": log}, indent=1))
        sys.exit(0)
Path(sys.argv[1]).write_text(json.dumps({"settled": False, "windows": log}, indent=1))
sys.exit(3)
