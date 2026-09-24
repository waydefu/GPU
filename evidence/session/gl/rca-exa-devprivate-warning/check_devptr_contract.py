#!/usr/bin/env python3
"""Static oracle for the EXA devPrivate.ptr contract in lorie's InitOutput.c.

EXA (driver mode) requires pPixmap->devPrivate.ptr == NULL whenever the pixmap is not inside
an exaPrepareAccess()/exaFinishAccess() pair (xserver exa.c ExaDoPrepareAccess check).
The driver hook loriePrepareAccess() may set it, because EXA calls it from inside the pair and
exaFinishAccess() clears it again. Anything else that leaves a non-NULL value breaks the contract.

Rules (each hit = one violation):
  D  direct call of loriePrepareAccess()/lorieFinishAccess() outside the allowed wrapper functions
  W  assignment of a non-NULL value to ->devPrivate.ptr outside loriePrepareAccess() and the wrappers
Exit 0 = GREEN (no violation), 1 = RED.
"""
import re
import sys

ALLOWED_WRAPPERS = {"lorieInternalPrepareAccess", "lorieInternalFinishAccess"}
HOOK = "loriePrepareAccess"

# function definitions start at column 0 (this file's style); the signature may span lines
FUNC_HEAD = re.compile(r"^(?!typedef|return|if|for|while|switch|else|do|struct|enum|#)[A-Za-z_][\w\s\*]*?\b(\w+)\s*\(")
DIRECT = re.compile(r"\b(loriePrepareAccess|lorieFinishAccess)\s*\(")
WRITE = re.compile(r"devPrivate\.ptr\s*=(?!=)\s*([^;]+);")


def scan(path):
    fn = None
    pending = None
    hits = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f, 1):
            m = FUNC_HEAD.match(line)
            if m and not line.rstrip().endswith(";"):
                pending = m.group(1)
            if pending and line.rstrip().endswith("{"):
                fn, pending = pending, None
            elif pending and line.rstrip().endswith(";"):
                pending = None
            code = line.split("//")[0]
            if code.lstrip().startswith(("*", "/*")):
                continue
            for d in DIRECT.finditer(code):
                # prototypes and the ExaDriverRec initializer are not calls
                if re.match(r"^\s*(Bool|void)\s+(loriePrepareAccess|lorieFinishAccess)\s*\(", code):
                    continue
                if ".PrepareAccess" in code or ".FinishAccess" in code:
                    continue
                if fn in ALLOWED_WRAPPERS:
                    continue
                hits.append(("D", n, fn, d.group(1)))
            w = WRITE.search(code)
            if w and w.group(1).strip() != "NULL" and fn not in ALLOWED_WRAPPERS and fn != HOOK:
                hits.append(("W", n, fn, w.group(1).strip()))
    return hits


def main():
    rc = 0
    for path in sys.argv[1:]:
        hits = scan(path)
        verdict = "RED" if hits else "GREEN"
        print(f"{verdict} {path} violations={len(hits)} "
              f"D={sum(h[0] == 'D' for h in hits)} W={sum(h[0] == 'W' for h in hits)}")
        for kind, n, fn, what in hits:
            print(f"  {kind} line={n} fn={fn} {what}")
        rc |= 1 if hits else 0
    return rc


if __name__ == "__main__":
    sys.exit(main())
