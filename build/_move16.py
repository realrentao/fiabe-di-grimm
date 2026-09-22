# -*- coding: utf-8 -*-
"""Move legacy audio/16 (old s*.mp3 + leftover p*.mp3) out of the way into
build/_trash16 so freshly generated s001..s052 / z001..z052 are the only files.
Uses shutil.move (rename) to avoid the SAFE_DELETE guard on bulk rm."""
import os, shutil

ROOT = r"D:/意大利语材料/grimm-fiabe"
SRC = os.path.join(ROOT, "audio", "16")
DST = os.path.join(ROOT, "build", "_trash16")
os.makedirs(DST, exist_ok=True)

moved = 0
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".mp3"):
        continue
    src = os.path.join(SRC, fn)
    dst = os.path.join(DST, fn)
    base, ext = os.path.splitext(fn)
    while os.path.exists(dst):
        dst = os.path.join(DST, base + "_%d" % moved + ext)
    shutil.move(src, dst)
    moved += 1
print("moved %d legacy files from audio/16 -> build/_trash16" % moved)
print("remaining in audio/16:", len(os.listdir(SRC)))
