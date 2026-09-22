# -*- coding: utf-8 -*-
import os, shutil
src = r"D:/意大利语材料/grimm-fiabe/audio/14"
dst = r"D:/意大利语材料/grimm-fiabe/build/_trash14"
os.makedirs(dst, exist_ok=True)
moved = 0
for f in os.listdir(src):
    if f.startswith("s") or f.startswith("p"):
        shutil.move(os.path.join(src, f), os.path.join(dst, f))
        moved += 1
print("moved s*/p* =", moved)
print("remaining in audio/14:", sorted(os.listdir(src)))
