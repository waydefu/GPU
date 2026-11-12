# S3 X11 Closure (13 symbols — complete, machine-checked from `/tmp/b3a-link.log`)

Proven top line: **live `Display*` = provably NO** for all 13 (see chains).
Therefore this is NOT an architecture-level runtime dependency on full libX11;
it is dead client-side Xlib sections pulled in by `--whole-archive`.

## Symbol → object → function → chain → verdict

| # | Undefined symbol | Normally defined in | Referencing object:function | Caller chain to server | Live Display*? |
|---|---|---|---|---|---|
| 1 | `XGetKeyboardMapping` | libX11 (absent since 2023 `43b789b`) | KeyBind.c.o:`_XKeyInitialize` | `_XKeyInitialize` ← XLookupKeysym-family ← zero in-link callers; needs `Display*`; no `XOpenDisplay` in any linked code (only unbuilt `hw/{ephyr,xnest,xquartz}` backends) | NO |
| 2 | `XGetModifierMapping` | libX11 | KeyBind.c.o:`_XKeyInitialize` | same as #1 | NO |
| 3 | `XFreeModifiermap` | libX11 | KeyBind.c.o:`_XKeyInitialize` | same as #1 | NO |
| 4 | `_XFreeMutex_fn` | libX11 locking | Xrm.c.o:`XrmDestroyDatabase` | `XrmDestroyDatabase` ← zero callers in lorie/xserver/Xfont/xkbfile | NO |
| 5–10 | `_XkbInitReadBuffer`, `_XkbGetReadBufferCountedString`, `_XkbGetReadBufferPtr`, `_XkbSkipReadBufferData`, `_XkbCopyFromReadBuffer`, `_XkbFreeReadBuffer` | libX11 XKB | XKBGeom.c.o:`_XkbReadGetGeometryReply` (static) | ← `XkbGetGeometry` ← `libxkbfile/srvmisc.c:100`, and libxkbfile is NOT linked; no other callers | NO |
| 11 | `XkbUseExtension` | libX11 | XKBGeom.c.o:`XkbGetGeometry` | same as #5–10 | NO |
| 12 | `_XGetRequest` | libX11 | XKBGeom.c.o:`XkbGetGeometry` | same as #5–10 | NO |
| 13 | `_XReply` | libX11 (`xcb_io.c`, present in tree but never compiled into any linked archive) | XKBGeom.c.o:`XkbGetGeometry` | same as #5–10 | NO |

Notes:

- `XkbGetGeometry`'s sole caller (`srvmisc.c:100`, itself NULL-guarded on `dpy`)
  lives in `libxkbfile`, which is not on the link line — so inside this link the
  whole geometry-protocol path is dead code, pulled only by `--whole-archive`.
- `XKBGeom.c` / protocol helpers are unconditional in libX11 1.8.13 (only a
  `HAVE_CONFIG_H` guard at top); no compile-flag magic can remove the
  references. The fix must be at target/object granularity, not flags.
- Preferred direction (not yet approved): drop/isolate the dead client-side
  objects from the `xkbcomp` static target instead of stubbing Xlib. Stubbing
  is explicitly rejected (a stub that ever executed would corrupt XKB behavior
  loudly-or-silently; and all 13 are proven unreachable, so stubs buy nothing).
