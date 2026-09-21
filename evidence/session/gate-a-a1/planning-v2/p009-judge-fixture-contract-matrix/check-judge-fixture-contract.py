#!/usr/bin/env python3
"""V2-P009 — judge <-> fixture contract matrix gate.

Host-only, read-only, zero device interaction. Run BEFORE any runtime grant.

Why this exists: judge_c1 requires observation phases that cell_c1 structurally
cannot emit, so R8-C1 could never pass no matter how many attempts were spent.
That mismatch sat behind the STABLE_AFTER ordering regression for six runner
generations and eight attempts. This gate makes the same class of defect cheap
to detect: it reads the judge and the fixture and reports, per cell, any phase
the judge demands whose producing client request the fixture never sends.

Limits (stated so the output is not over-read): this is static analysis over
source text, not a proof. It detects the "judge demands a phase the fixture can
never trigger" class only. A clean run does NOT mean a cell will pass.

Exit: 0 = no mismatch, 1 = mismatch found, 2 = could not analyse.
"""
from __future__ import annotations
import re, sys, pathlib

R8 = pathlib.Path("/root/projects/GPU加速/src/f8-ahb-gatea-r7-p1-arm/tests/r8")
JUDGE   = R8 / "judge-r8-v2.py"
FIXTURE = R8 / "p_r8_lifecycle.c"

# phases that require the CLIENT to send a specific request before the
# server/renderer will ever emit them
PHASE_NEEDS_REQUEST = {
    "X_CHECKPOINT":    "r8_checkpoint",
    "R_DESTROY_STAGE": "r8_register",
    "R_ACK_SETTLED":   "r8_register",
}
# helpers in the judge that imply phase requirements beyond require_obs()
HELPER_IMPLIES = {
    "destroy_before_x_release": ["R_DESTROY_STAGE", "R_ACK_SETTLED", "X_DESTRUCTOR_EXIT"],
}
# judge function -> fixture function
CELLS = {
    "R8-C1":            ("judge_c1",           "cell_c1"),
    "R8-C2":            ("judge_c2",           "cell_c2"),
    "R8-C3-window":     ("judge_c3",           "cell_c3_window"),
    "R8-C3-disconnect": ("judge_c3",           "cell_c1"),   # c3-disconnect reuses cell_c1
    "R8-C4":            ("judge_c4",           "cell_c4"),
    "R8-C5-full":       ("judge_c5_full",      "cell_c5_full"),
    "R8-C5-overflow":   ("judge_c5_overflow",  "cell_c5_overflow"),
    "R8-D":             ("judge_d",            "cell_d"),
    "R8-P1":            ("judge_p1",           "cell_p"),
    "R8-P2":            ("judge_p2",           "cell_p"),
}

def strip_py_comments(s: str) -> str:
    return re.sub(r'#[^\n]*', '', s)

def strip_c_comments(s: str) -> str:
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    return re.sub(r'//[^\n]*', '', s)

def bodies(src: str, pattern: str) -> dict[str, str]:
    hits = [(m.start(), m.group(1)) for m in re.finditer(pattern, src, re.M)]
    hits.append((len(src), "<eof>"))
    return {hits[i][1]: src[hits[i][0]:hits[i+1][0]] for i in range(len(hits)-1)}

def main() -> int:
    for f in (JUDGE, FIXTURE):
        if not f.is_file():
            print(f"ANALYSIS_FAILED missing {f}", file=sys.stderr); return 2
    jb = bodies(JUDGE.read_text(encoding="utf-8"),   r'^def (judge_[a-z0-9_]+)\(')
    fb = bodies(FIXTURE.read_text(encoding="utf-8"), r'^static int (cell_[a-z0-9_]+)\(')

    rows, mismatches = [], []
    for cell, (jf, cf) in CELLS.items():
        j, c = jb.get(jf), fb.get(cf)
        if j is None or c is None:
            print(f"ANALYSIS_FAILED {cell}: judge={jf in jb} fixture={cf in fb}", file=sys.stderr)
            return 2
        # comments must not count as code: naming a helper in a comment is not
        # calling it (this gate reported a false UNREACHABLE for exactly that
        # reason on 2026-09-21, right after judge_c1 was fixed)
        j, c = strip_py_comments(j), strip_c_comments(c)
        required = set(re.findall(r'require_obs\([^,]+,\s*"([A-Z0-9_]+)"', j))
        for helper, implied in HELPER_IMPLIES.items():
            if re.search(rf'\b{helper}\(', j):
                required.update(implied)
        sends = {r for r in ("r8_query", "r8_register", "r8_checkpoint") if re.search(rf'\b{r}\(', c)}
        missing = sorted(p for p in required
                         if p in PHASE_NEEDS_REQUEST and PHASE_NEEDS_REQUEST[p] not in sends)
        status = "UNREACHABLE" if missing else "ok"
        if missing:
            mismatches.append((cell, jf, cf, missing))
        rows.append((cell, jf, cf,
                     ",".join(sorted(required)) or "-",
                     ",".join(sorted(sends)) or "-",
                     ",".join(missing) or "-", status))

    print("cell\tjudge\tfixture\tjudge_requires\tfixture_sends\tunsatisfiable\tstatus")
    for r in rows:
        print("\t".join(r))
    print()
    if mismatches:
        print(f"VERDICT CONTRACT_MISMATCH  {len(mismatches)}/{len(CELLS)} cells unreachable")
        for cell, jf, cf, missing in mismatches:
            need = sorted({PHASE_NEEDS_REQUEST[p] for p in missing})
            print(f"  {cell}: {jf} requires {', '.join(missing)}; "
                  f"{cf} never sends {', '.join(need)}")
        print("\nDo not spend an attempt on an UNREACHABLE cell. DESIGN_REQUIRED (§19.1 Q1).")
        return 1
    print("VERDICT CONTRACT_CONSISTENT  (no cell demands a phase its fixture cannot trigger)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
