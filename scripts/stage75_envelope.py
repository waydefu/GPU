#!/usr/bin/env python3
"""Peak Python heap of one governed tool call (tracemalloc), for the Stage 7.5 capacity table."""

from __future__ import annotations

import json
import sys
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f8_hybrid2_budget as budget  # noqa: E402
from f8_hybrid2_policy import Policy  # noqa: E402
from f8_hybrid2_tools import MCPToolEngine, RequestContext  # noqa: E402
from stage75_matrix import HEAVY, NORMAL  # noqa: E402


def main() -> int:
    ws, git_bin, tmp = sys.argv[1], sys.argv[2], sys.argv[3]
    engine = MCPToolEngine(Policy([("/fixture", ws)], home=tmp, tmp=tmp, single_thread_git=True), git_bin=git_bin,
                           parse_budget=budget.GOVERNED.tool_parse_budget)
    out = {"python": sys.version.split()[0]}
    for name, args in HEAVY + NORMAL:
        tracemalloc.start()
        resp = engine.call_tool(1, {"name": name, "arguments": args}, RequestContext(1, 300))
        raw = (json.dumps(resp, ensure_ascii=False) + "\n").encode()
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        assert "result" in resp and not resp["result"]["isError"], str(resp)[:300]
        key = f"{name}:{json.dumps(args, sort_keys=True)}"
        out[key] = {"peak_kib": peak // 1024, "response_bytes": len(raw)}
        del resp, raw
    out["max_peak_kib"] = max(v["peak_kib"] for k, v in out.items() if isinstance(v, dict))
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
