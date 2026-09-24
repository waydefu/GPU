#!/usr/bin/env python3
"""Checker-validation mutants of f592241 InitOutput.c (host-only, never compiled, not a patch).

usage: make_mutants.py <InitOutput.f592241.c> <outdir>
  M1-fix2        every direct loriePrepareAccess/lorieFinishAccess call in the 7 internal CPU
                 helpers goes through a save/restore wrapper (proposal Fix-2)
  M2-fix2-fix3   M1 + the four Gate A non-NULL devPrivate.ptr writes removed (proposal Fix-3)
  M3-must-red    M2 with one wrapper call turned back into a direct call (the checker MUST go red)
"""
import os
import re
import sys

DIRECT_LINES = {2166, 2167, 2181, 2186, 2302, 2316, 2326, 2344, 2491, 2493, 2494, 2508, 2509,
                3881, 3883, 3884, 3897, 3898, 3910, 3930}
WRAPPERS = """static Bool lorieInternalPrepareAccess(PixmapPtr p, int index, void **saved) {
    *saved = p->devPrivate.ptr;
    if (loriePrepareAccess(p, index))
        return TRUE;
    p->devPrivate.ptr = *saved;
    return FALSE;
}
static void lorieInternalFinishAccess(PixmapPtr p, int index, void *saved) {
    lorieFinishAccess(p, index);
    p->devPrivate.ptr = saved;
}"""
GATEA_WRITES = ["        pSrcPix->devPrivate.ptr = sp->locked;\n",
                "        pDstPix->devPrivate.ptr = dp->locked;\n",
                "    exaGpuComp.src->devPrivate.ptr = sp->locked;\n",
                "    exaGpuComp.dst->devPrivate.ptr = dp->locked;\n"]


def main(src_path, outdir):
    src = open(src_path).read().split("\n")
    out = []
    for n, line in enumerate(src, 1):
        if n in DIRECT_LINES:
            line = re.sub(r"loriePrepareAccess\((\w+), (\w+)\)",
                          lambda m: f"lorieInternalPrepareAccess({m[1]}, {m[2]}, &sv_{m[1]})", line)
            line = re.sub(r"lorieFinishAccess\((\w+), (\w+)\)",
                          lambda m: f"lorieInternalFinishAccess({m[1]}, {m[2]}, sv_{m[1]})", line)
        out.append(line)
        if n == 2220:  # after the forward declarations of the two hooks
            out.append(WRAPPERS)
    m1 = "\n".join(out)
    m2 = m1
    for w in GATEA_WRITES:
        assert m2.count(w) == 1, w
        m2 = m2.replace(w, "")
    needle = ("lorieInternalPrepareAccess(dst, EXA_PREPARE_DEST, &sv_dst))\n        return;\n"
              "    d = dst->devPrivate.ptr;\n    dstride = dst->devKind;\n    bpp")
    assert m2.count(needle) == 1
    m3 = m2.replace(needle, needle.replace("lorieInternalPrepareAccess(dst, EXA_PREPARE_DEST, &sv_dst)",
                                           "loriePrepareAccess(dst, EXA_PREPARE_DEST)"))
    for name, text in (("M1-fix2", m1), ("M2-fix2-fix3", m2), ("M3-must-red", m3)):
        with open(os.path.join(outdir, f"InitOutput.{name}.c"), "w") as f:
            f.write(text)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
