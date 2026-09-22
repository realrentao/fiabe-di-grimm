# -*- coding: utf-8 -*-
"""Validate story 17 build output."""
import re, json, os

ROOT = r"D:/意大利语材料/grimm-fiabe"
SID = "17"

def load_st():
    t = open(os.path.join(ROOT, "data", "st", SID + ".js"), encoding="utf-8").read()
    i = t.index("window.__GRIMM_STORIES__['%s']" % SID)
    j = t.index("{", i)
    d = 0; e = None
    for k in range(j, len(t)):
        if t[k] == "{": d += 1
        elif t[k] == "}":
            d -= 1
            if d == 0: e = k + 1; break
    return json.loads(t[j:e])

errs = []
st = load_st()
paras = st["paras"]
N = len(paras)

# 1) pid continuous
pids = [p["pid"] for p in paras]
exp = ["s%03d" % n for n in range(1, N + 1)]
if pids != exp:
    errs.append("pid not continuous: %r" % pids)

# 2) audio paths
for p in paras:
    if p["audio"] != "audio/%s/%s.mp3" % (SID, p["pid"]):
        errs.append("bad audio %s" % p["pid"])
    if p["audio_zh"] != "audio/%s/%s.mp3" % (SID, "z%03d" % int(p["pid"][1:])):
        errs.append("bad audio_zh %s" % p["pid"])

# 3) zh checks
for p in paras:
    zh = p["zh"]
    if "「" in zh or "」" in zh:
        errs.append("%s has 「」" % p["pid"])
    if "——" in zh:
        errs.append("%s has em-dash ——" % p["pid"])
    if '"' in zh:
        errs.append("%s has ASCII straight quote" % p["pid"])
    if zh.strip() == "":
        errs.append("%s zh empty" % p["pid"])
    oc = zh.count("“"); cc = zh.count("”")
    if oc != cc:
        errs.append("%s zh quote unbalance “%d ”%d" % (p["pid"], oc, cc))

# 4) it «» balance
for p in paras:
    it = p["it"]
    if it.count("«") != it.count("»"):
        errs.append("%s it guillemet unbalance «%d »%d" % (p["pid"], it.count("«"), it.count("»")))

# 5) consistency across files
t = open(os.path.join(ROOT, "data", "stories.js"), encoding="utf-8").read()
m = re.search(r"window\.__GRIMM__ = (\{.*\});\s*$", t, re.S)
root = json.loads(m.group(1))
s17 = next(s for s in root["stories"] if s["id"] == SID)
if len(s17["paras"]) != N:
    errs.append("stories.js paras=%d != %d" % (len(s17["paras"]), N))
if s17["title_zh"] != st["title_zh"]:
    errs.append("stories.js title_zh mismatch")

t = open(os.path.join(ROOT, "data", "index.js"), encoding="utf-8").read()
m = re.search(r"window\.__GRIMM_INDEX__ = (\{.*\});\s*$", t, re.S)
idx = json.loads(m.group(1))
total = sum(len(s["paras"]) for s in root["stories"])
if idx["meta"]["para_count"] != total:
    errs.append("index para_count %d != recomputed %d" % (idx["meta"]["para_count"], total))
print("index para_count =", idx["meta"]["para_count"], "| recomputed =", total)

man = json.load(open(os.path.join(ROOT, "build", "audio_manifest.json"), encoding="utf-8"))
me = next((e for e in man if e["id"] == SID), None)
if me is None:
    errs.append("manifest missing id 17")
elif len(me["paras"]) != N:
    errs.append("manifest paras=%d != %d" % (len(me["paras"]), N))
else:
    for p, mp in zip(paras, me["paras"]):
        if mp["text"] != p["it"]:
            errs.append("%s manifest text mismatch" % p["pid"])

print("paras =", N, "| sections =", len(set(p["sec"] for p in paras)))
print("ERRORS:" if errs else "ALL OK")
for e in errs:
    print("  -", e)
print("exit", 1 if errs else 0)
