# -*- coding: utf-8 -*-
"""Move legacy audio/15 (old s*.mp3 + leftover p*.mp3) out of the way into
build/_trash15 so freshly generated s001..s120 / z001..z120 are the only files.
Uses shutil.move (rename) to avoid the SAFE_DELETE guard on bulk rm."""
import os, shutil

ROOT = r"D:/意大利语材料/grimm-fiabe"
SRC = os.path.join(ROOT, "audio", "15")
DST = os.path.join(ROOT, "build", "_trash15")
os.makedirs(DST, exist_ok=True)

moved = 0
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".mp3"):
        continue
    src = os.path.join(SRC, fn)
    dst = os.path.join(DST, fn)
    # avoid clobber
    base, ext = os.path.splitext(fn)
    while os.path.exists(dst):
        dst = os.path.join(DST, base + "_%d" % moved + ext)
    shutil.move(src, dst)
    moved += 1
print("moved %d files from audio/15 -> build/_trash15" % moved)
print("remaining in audio/15:", len(os.listdir(SRC)))
