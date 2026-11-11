#!/usr/bin/env python3
"""Decode x11gpu-flight.ring (256-slot X request dispatch recorder)."""
import os
import struct
import sys

MAGIC = 0x46524C31
CAP = 256
CORE = {
    1: "CreateWindow", 2: "ChangeWindowAttributes", 3: "GetWindowAttributes",
    4: "DestroyWindow", 5: "DestroySubwindows", 6: "ChangeSaveSet", 7: "ReparentWindow",
    8: "MapWindow", 9: "MapSubwindows", 10: "UnmapWindow", 11: "UnmapSubwindows",
    12: "ConfigureWindow", 13: "CirculateWindow", 14: "GetGeometry", 15: "QueryTree",
    16: "InternAtom", 17: "GetAtomName", 18: "ChangeProperty", 19: "DeleteProperty",
    20: "GetProperty", 21: "ListProperties", 22: "SetSelectionOwner", 23: "GetSelectionOwner",
    24: "ConvertSelection", 25: "SendEvent", 26: "GrabPointer", 27: "UngrabPointer",
    28: "GrabButton", 29: "UngrabButton", 30: "ChangeActivePointerGrab", 31: "GrabKeyboard",
    32: "UngrabKeyboard", 33: "GrabKey", 34: "UngrabKey", 35: "AllowEvents", 36: "GrabServer",
    37: "UngrabServer", 38: "QueryPointer", 39: "GetMotionEvents", 40: "TranslateCoords",
    41: "WarpPointer", 42: "SetInputFocus", 43: "GetInputFocus", 44: "QueryKeymap",
    45: "OpenFont", 46: "CloseFont", 47: "QueryFont", 48: "QueryTextExtents",
    49: "ListFonts", 50: "ListFontsWithInfo", 51: "SetFontPath", 52: "GetFontPath",
    53: "CreatePixmap", 54: "FreePixmap", 55: "CreateGC", 56: "ChangeGC", 57: "CopyGC",
    58: "SetDashes", 59: "SetClipRectangles", 60: "FreeGC", 61: "ClearArea", 62: "CopyArea",
    63: "CopyPlane", 64: "PolyPoint", 65: "PolyLine", 66: "PolySegment", 67: "PolyRectangle",
    68: "PolyArc", 69: "FillPoly", 70: "PolyFillRectangle", 71: "PolyFillArc",
    72: "PutImage", 73: "GetImage", 74: "PolyText8", 75: "PolyText16", 76: "ImageText8",
    77: "ImageText16", 78: "CreateColormap", 79: "FreeColormap", 80: "CopyColormapAndFree",
    81: "InstallColormap", 82: "UninstallColormap", 83: "ListInstalledColormaps",
    84: "AllocColor", 85: "AllocNamedColor", 86: "AllocColorCells", 87: "AllocColorPlanes",
    88: "FreeColors", 89: "StoreColors", 90: "StoreNamedColor", 91: "QueryColors",
    92: "LookupColor", 93: "CreateCursor", 94: "CreateGlyphCursor", 95: "FreeCursor",
    96: "RecolorCursor", 97: "QueryBestSize", 98: "QueryExtension", 99: "ListExtensions",
    100: "ChangeKeyboardMapping", 101: "GetKeyboardMapping", 102: "ChangeKeyboardControl",
    103: "GetKeyboardControl", 104: "Bell", 105: "ChangePointerControl", 106: "GetPointerControl",
    107: "SetScreenSaver", 108: "GetScreenSaver", 109: "ChangeHosts", 110: "ListHosts",
    111: "SetAccessControl", 112: "SetCloseDownMode", 113: "KillClient", 114: "RotateProperties",
    115: "ForceScreenSaver", 116: "SetPointerMapping", 117: "GetPointerMapping",
    118: "SetModifierMapping", 119: "GetModifierMapping", 127: "NoOperation",
}
RENDER = {
    0: "QueryVersion", 1: "QueryPictFormats", 2: "QueryPictIndexValues", 3: "QueryDithers",
    4: "CreatePicture", 5: "ChangePicture", 6: "SetPictureClipRectangles", 7: "FreePicture",
    8: "Composite", 9: "Trapezoids", 10: "Triangles", 11: "TriStrip", 12: "TriFan",
    13: "CreateGlyphSet", 14: "ReferenceGlyphSet", 15: "FreeGlyphSet", 16: "AddGlyphs",
    17: "FreeGlyphs", 18: "CompositeGlyphs8", 19: "CompositeGlyphs16", 20: "CompositeGlyphs32",
    21: "FillRectangles", 22: "CreateCursor", 23: "SetPictureTransform", 24: "QueryFilters",
    25: "SetPictureFilter", 26: "CreateAnimCursor", 27: "AddTraps", 28: "CreateSolidFill",
    29: "CreateLinearGradient", 30: "CreateRadialGradient", 31: "CreateConicalGradient",
}
DRI3 = {
    0: "QueryVersion", 1: "Open", 2: "PixmapFromBuffer", 3: "BufferFromPixmap",
    4: "FenceFromFD", 5: "FDFromFence", 6: "GetSupportedModifiers", 7: "PixmapFromBuffers",
    8: "BuffersFromPixmap", 200: "AHardwareBufferFromPixmap",
}
PRESENT = {0: "QueryVersion", 1: "Pixmap", 2: "NotifyMSC", 3: "SelectInput", 4: "QueryCapabilities"}
XFIXES = {
    0: "QueryVersion", 1: "ChangeSaveSet", 2: "SelectSelectionInput", 3: "SelectCursorInput",
    4: "GetCursorImage", 12: "CreateRegion", 13: "CreateRegionFromBitmap",
    14: "CreateRegionFromWindow", 15: "CreateRegionFromGC", 16: "CreateRegionFromPicture",
    17: "DestroyRegion", 18: "SetRegion", 19: "CopyRegion", 20: "UnionRegion",
    21: "IntersectRegion", 22: "SubtractRegion", 23: "InvertRegion", 24: "TranslateRegion",
    25: "RegionExtents", 26: "FetchRegion", 27: "SetGCClipRegion", 28: "SetWindowShapeRegion",
    29: "SetPictureClipRegion", 30: "SetCursorName", 31: "GetCursorName", 32: "GetCursorImageAndName",
    33: "ChangeCursor", 34: "ChangeCursorByName",
}
COMPOSITE = {
    0: "QueryVersion", 1: "RedirectWindow", 2: "RedirectSubwindows", 3: "UnredirectWindow",
    4: "UnredirectSubwindows", 5: "CreateRegionFromBorderClip", 6: "NameWindowPixmap",
    7: "GetOverlayWindow", 8: "ReleaseOverlayWindow",
}
DAMAGE = {0: "QueryVersion", 1: "Create", 2: "Destroy", 3: "Subtract", 4: "Add"}
SHAPE = {0: "QueryVersion", 1: "Rectangles", 2: "Mask", 3: "Combine", 4: "Offset",
         5: "QueryExtents", 6: "SelectInput", 7: "InputSelected", 8: "GetRectangles"}
RANDR = {
    0: "QueryVersion", 2: "SetScreenConfig", 4: "SelectInput", 5: "GetScreenInfo",
    8: "GetScreenSizeRange", 9: "SetScreenSize", 20: "GetCrtcInfo", 21: "SetCrtcConfig",
    25: "SetCrtcTransform", 26: "GetCrtcTransform",
}

ENT = struct.Struct("<IIHHBB h 16s")  # seq req_len minor client major phase result head
HDR = struct.Struct("<IIII")


def name_of(major, minor, major_name):
    if major < 128:
        return CORE.get(major, f"core-{major}")
    n = (major_name or "").lower()
    table = None
    if "render" in n:
        table = RENDER
    elif "dri3" in n:
        table = DRI3
    elif "present" in n:
        table = PRESENT
    elif "xfixes" in n or n == "fixes":
        table = XFIXES
    elif "composite" in n:
        table = COMPOSITE
    elif "damage" in n:
        table = DAMAGE
    elif "shape" in n:
        table = SHAPE
    elif "randr" in n:
        table = RANDR
    minor_s = table.get(minor, str(minor)) if table else str(minor)
    return f"{major_name or 'ext'} {minor_s}"


def decode(path):
    data = open(path, "rb").read()
    magic, cap, w, _pad = HDR.unpack_from(data, 0)
    if magic != MAGIC:
        print(f"BAD magic 0x{magic:08x} (want 0x{MAGIC:08x})")
        return 1
    n = min(w, cap)
    start = w - n
    print(f"path={path} magic=OK cap={cap} w={w} showing={n} oldest→newest")
    last = None
    for i in range(n):
        off = 16 + ((start + i) % cap) * ENT.size
        seq, req_len, minor, client, major, phase, result, head = ENT.unpack_from(data, off)
        maj_name = CORE.get(major, "")
        label = name_of(major, minor, maj_name if major < 128 else "")
        rec = {
            "i": i, "seq": seq, "cli": client, "major": major, "minor": minor,
            "len": req_len, "phase": phase, "result": result, "head": head.hex(),
            "name": label, "last": i + 1 == n,
        }
        last = rec
        mark = "LAST " if rec["last"] else ""
        ph = "ENTER" if phase == 1 else ("LEAVE" if phase == 2 else str(phase))
        print(f"{mark}{i:03d} seq={seq} cli={client} op={major}.{minor} {label} len={req_len} {ph} r={result} head={head.hex()}")
    if last:
        print("--- LAST REQUEST ---")
        print(f"seq={last['seq']} cli={last['cli']} op={last['major']}.{last['minor']} {last['name']} "
              f"phase={'IN-HANDLER' if last['phase']==1 else 'completed'} head={last['head']}")
    return 0


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/x11gpu-flight.ring"
    if not os.path.exists(path):
        print("missing", path)
        sys.exit(2)
    sys.exit(decode(path))
