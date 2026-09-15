# -*- coding: utf-8 -*-
"""Split data/stories.js (2.6MB monolith) into:
  data/index.js      -> window.__GRIMM_INDEX__ = {meta, stories:[{id,title_it,title_zh}]}   (~30KB, catalog page)
  data/st/<id>.js    -> window.__GRIMM_STORY__ = {full story object}                        (~per story, reader page)
"""
import json, os, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "stories.js")
ST_DIR = os.path.join(ROOT, "data", "st")
os.makedirs(ST_DIR, exist_ok=True)

txt = io.open(SRC, encoding="utf-8").read()
# strip "window.__GRIMM__ = " prefix and trailing ";"
txt = txt.strip()
assert txt.startswith("window.__GRIMM__"), "unexpected format"
json_txt = txt[txt.index("{"):].strip().rstrip(";")
data = json.loads(json_txt)

meta = data["meta"]
stories = data["stories"]
# 数字序排序（01..174），否则字典序会把 100+ 插到 10 后面
stories.sort(key=lambda s: int(s["id"]))
print("stories:", len(stories), "paras:", sum(len(s["paras"]) for s in stories))

# 1) index
idx = {"meta": meta, "stories": [{"id": s["id"], "title_it": s["title_it"], "title_zh": s["title_zh"]} for s in stories]}
out = "window.__GRIMM_INDEX__ = " + json.dumps(idx, ensure_ascii=False, separators=(",", ":")) + ";\n"
io.open(os.path.join(ROOT, "data", "index.js"), "w", encoding="utf-8", newline="\n").write(out)
print("index.js:", os.path.getsize(os.path.join(ROOT, "data", "index.js")), "bytes")

# 2) per-story files
total = 0
for s in stories:
    out = ("window.__GRIMM_STORIES__ = window.__GRIMM_STORIES__ || {};\n"
           "window.__GRIMM_STORIES__['" + s["id"] + "'] = "
           + json.dumps(s, ensure_ascii=False, separators=(",", ":")) + ";\n")
    p = os.path.join(ST_DIR, s["id"] + ".js")
    io.open(p, "w", encoding="utf-8", newline="\n").write(out)
    total += os.path.getsize(p)
print("st files:", len(stories), "total:", total, "bytes, avg:", total // max(1, len(stories)))
