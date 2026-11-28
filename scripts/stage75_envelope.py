#!/usr/bin/env python3
"""Peak Python heap of one governed tool call (tracemalloc), for the Stage 7.5 capacity table."""

from __future__ import annotations

import json
import os
import resource
import sys
import threading
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f8_hybrid2_budget as budget  # noqa: E402
from f8_hybrid2_policy import Policy  # noqa: E402
from f8_hybrid2_tools import MCPToolEngine, RequestContext  # noqa: E402
from stage75_matrix import HEAVY, NORMAL, descendants  # noqa: E402


def _child_pss(stop: threading.Event, peak: dict) -> None:
    """Poll descendants (PPID scan) for short-lived git/regex children."""
    me = os.getpid()
    while not stop.wait(0.005):
        for pid in descendants([me]):
            if pid == me:
                continue
            try:
                pss = int(Path(f"/proc/{pid}/smaps_rollup").read_text().split("Pss:", 1)[1].split()[0])
                comm = Path(f"/proc/{pid}/comm").read_text().strip()
            except (OSError, ValueError, IndexError):
                continue
            peak[comm] = max(peak.get(comm, 0), pss)


def main() -> int:
    ws, git_bin, tmp = sys.argv[1], sys.argv[2], sys.argv[3]
    engine = MCPToolEngine(Policy([("/fixture", ws)], home=tmp, tmp=tmp, single_thread_git=True), git_bin=git_bin,
                           parse_budget=budget.GOVERNED.tool_parse_budget)
    out = {"python": sys.version.split()[0]}
    stop, child_peak = threading.Event(), {}
    sampler = threading.Thread(target=_child_pss, args=(stop, child_peak), daemon=True)
    sampler.start()
    regex = ("repo_text_search", {"root": "/fixture/corpus.txt", "pattern": "need+le", "max_matches": 5000})
    for name, args in HEAVY + NORMAL + [regex]:
        tracemalloc.start()
        resp = engine.call_tool(1, {"name": name, "arguments": args}, RequestContext(1, 300))
        raw = (json.dumps(resp, ensure_ascii=False) + "\n").encode()
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        assert "result" in resp and not resp["result"]["isError"], str(resp)[:300]
        key = f"{name}:{json.dumps(args, sort_keys=True)}"
        out[key] = {"peak_kib": peak // 1024, "response_bytes": len(raw)}
        del resp, raw
    # git and regex-worker children: max RSS (>= PSS) of any child this process waited for.
    stop.set()
    sampler.join()
    out["child_peak_pss_kib"] = child_peak
    out["child_maxrss_kib"] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    out["max_peak_kib"] = max(v["peak_kib"] for v in out.values() if isinstance(v, dict) and "peak_kib" in v)
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
