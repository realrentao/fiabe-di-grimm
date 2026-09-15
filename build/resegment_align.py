# -*- coding: utf-8 -*-
"""Re-segment Italian into balanced paragraphs and align Chinese SENTENCES to them.

Two problems fixed vs. the old version:
1. Italian paragraphs were taken verbatim from the .docx -> some stories were one
   giant block (e.g. #75 = 1 Italian paragraph) while others were one sentence per
   paragraph. We now split Italian into sentences and regroup into BALANCED
   paragraphs (target ~120 chars, 2-4 sentences, cap 260 chars).
2. Chinese alignment was paragraph-level and imprecise. We now split Chinese into
   sentences and ask the LLM (glm-4-flash) to map EACH Chinese sentence to the
   Italian paragraph it belongs to -> precise sentence-level 对照.

The LLM outputs indices only (a `map` of length = #Chinese sentences), so it cannot
invent text. On any invalid output we fall back to a deterministic sentence-level
length-ratio alignment.

Outputs:
  data/stories.js          (window.__GRIMM__ = {...})
  build/audio_manifest.json (for gen_audio.py; text = the NEW Italian chunk)
Per-story results cached in build/reseg_cache.json (resumable).
"""
import os, sys, json, glob, re, time, ssl, urllib.request, argparse
sys.stdout.reconfigure(encoding="utf-8")

import parse_grimm as P

OUT = P.OUT
CACHE = os.path.join(OUT, "build", "reseg_cache.json")
MODEL = "glm-4-flash"
KEY = os.environ.get("ZHIPUAI_API_KEY", "")
assert KEY, "ZHIPUAI_API_KEY not set"

CTX = ssl.create_default_context()

# ----------------------------------------------------------------------------
# Sentence splitting
# ----------------------------------------------------------------------------
IT_ABBR = r"(?:Sig|Sp|Prof|Dott|Ecc|Cfr|Es|N|Dr|Avv|Gen|Cap|Col|Spett|Sig\.ra|p\.es|p\.e)"
SENT_SPLIT_IT = re.compile(r"(?<=[.!?])\s+")
SENT_SPLIT_ZH = re.compile(r"(?<=[。！？；…!?])")


def split_sentences_it(text):
    """Split Italian text into sentences, protecting common abbreviations."""
    text = text.replace("\u00a0", " ")
    # protect abbreviation dots so they don't trigger a split
    prot = []

    def _p(m):
        prot.append(m.group(0))
        return "\x00%d\x00" % (len(prot) - 1)

    text = re.sub(IT_ABBR + r"\.", _p, text, flags=re.I)
    parts = SENT_SPLIT_IT.split(text)
    out = []
    for p in parts:
        p = p.replace("\x00", ".")
        p = p.strip()
        if p:
            out.append(p)
    return out


def split_sentences_zh(text):
    parts = SENT_SPLIT_ZH.split(text)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # drop pure-punctuation fragments (e.g. a lone quotation mark)
        if len(re.sub(r'[\s\W]', '', p)) < 2:
            if out:
                out[-1] = out[-1] + p
            continue
        # merge very short fragments into the previous sentence
        if out and len(p) < 4:
            out[-1] = out[-1] + p
            continue
        out.append(p)
    return out


def resegment(sentences, target=170, min_s=2, max_s=5, max_chars=520, min_merge=35):
    """Group a flat sentence list into balanced paragraphs.

    Closes a paragraph when: reached max sentences, OR reached target length with
    at least min sentences, OR the just-added sentence itself is >= max_chars.
    Also closes early if adding the next sentence would exceed max_chars.
    Finally merges any very short stray fragment into the previous paragraph.
    """
    paras = []
    cur = []
    clen = 0
    for s in sentences:
        if cur and clen + len(s) > max_chars:
            paras.append(" ".join(cur))
            cur = []
            clen = 0
        cur.append(s)
        clen += len(s)
        if (len(cur) >= max_s) or (clen >= target and len(cur) >= min_s) or len(s) >= max_chars:
            paras.append(" ".join(cur))
            cur = []
            clen = 0
    if cur:
        paras.append(" ".join(cur))
    # merge tiny stray fragments into the previous paragraph
    out = []
    for p in paras:
        if out and len(p) < min_merge:
            out[-1] = out[-1] + " " + p
        else:
            out.append(p)
    return out


# ----------------------------------------------------------------------------
# LLM
# ----------------------------------------------------------------------------
def call_llm(messages, maxtry=4):
    body = json.dumps({
        "model": MODEL,
        "messages": messages,
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    last = None
    for attempt in range(maxtry):
        try:
            req = urllib.request.Request(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                data=body,
                headers={"Authorization": f"Bearer {KEY}",
                          "Content-Type": "application/json"},
                method="POST")
            with urllib.request.urlopen(req, context=CTX, timeout=90) as r:
                resp = json.loads(r.read().decode("utf-8"))
            return resp["choices"][0]["message"]["content"]
        except Exception as e:
            last = e
            msg = str(e)
            if "429" in msg:
                time.sleep(8 * (attempt + 1))
            else:
                time.sleep(3)
    raise RuntimeError("llm failed: %r" % last)


def build_prompt(it_chunks, zh_sents):
    m = len(it_chunks)
    k = len(zh_sents)
    it_txt = "\n".join("[%d] %s" % (i + 1, p) for i, p in enumerate(it_chunks))
    zh_txt = "\n".join("(%d) %s" % (i + 1, p) for i, p in enumerate(zh_sents))
    sysmsg = ("Sei un allineatore di frasi. Leggi un testo italiano suddiviso in "
              "paragrafi e la sua traduzione cinese suddivisa in frasi. Per OGNI "
              "frase cinese devi indicare a quale paragrafo italiano appartiene. "
              "Rispondi SOLO con JSON valido.")
    note = (" (ci sono piu frasi cinesi che paragrafi italiani, quindi piu frasi "
            "cinesi possono appartenere ALLO STESSO paragrafo italiano)" if k >= m
            else " (ci sono meno frasi cinesi che paragrafi italiani)")
    usr = ("Paragrafi italiani (in ordine):\n" + it_txt + "\n\n"
           "Frasi cinesi (in ordine):\n" + zh_txt + "\n\n"
           "Per ciascuna delle " + str(k) + " frasi cinesi (dall'1 al " + str(k) +
           "), restituisci l'indice del paragrafo italiano (1.." + str(m) +
           ") a cui appartiene." + note + ".\nRegole:\n"
           "- gli indici devono essere NON-DECRESCENTI (il testo e' in ordine);\n"
           "- ogni paragrafo italiano 1.." + str(m) + " deve comparire ALMENO UNA "
           "volta" + ("" if k >= m else " (ammesso che ci siano abbastanza frasi)") +
           ".\nRestituisci SOLO JSON: {\"map\":[i1,i2,...,i" + str(k) +
           "]} dove ogni i_k e' un intero da 1 a " + str(m) + ".")
    return [{"role": "system", "content": sysmsg},
            {"role": "user", "content": usr}]


def parse_map(text, m, k):
    """model returns {"map":[i1..ik]} (each Chinese sentence -> Italian chunk).
    Returns the map list, or None if invalid."""
    try:
        obj = json.loads(text)
    except Exception:
        return None
    mp = obj.get("map") if isinstance(obj, dict) else None
    if not isinstance(mp, list) or len(mp) != k:
        return None
    if any(not isinstance(x, int) or x < 1 or x > m for x in mp):
        return None
    for i in range(k - 1):
        if mp[i] > mp[i + 1]:
            return None
    if k >= m and set(mp) != set(range(1, m + 1)):
        return None
    return mp


def align_sentences_ratio(it_chunks, zh_sents):
    """Deterministic fallback: cumulative-length ratio at sentence level."""
    m, k = len(it_chunks), len(zh_sents)
    if m == 0 or k == 0:
        return [1] * k if k else []
    it_lens = [len(x) for x in it_chunks]
    zh_lens = [len(x) for x in zh_sents]
    total_it = sum(it_lens) or 1
    total_zh = sum(zh_lens) or 1
    zh_cum = []
    c = 0
    for l in zh_lens:
        c += l
        zh_cum.append(c)
    mp = []
    zh_pos = 0
    it_cum = 0
    for i, il in enumerate(it_lens):
        it_cum += il
        target = it_cum * total_zh / total_it
        j = zh_pos
        while j < k and zh_cum[j] < target:
            j += 1
        end = max(zh_pos, min(j, k - 1))
        for _ in range(zh_pos, end + 1):
            mp.append(i + 1)
        zh_pos = end + 1
    while len(mp) < k:
        mp.append(m)
    return mp[:k]


def align_story(it_chunks, zh_sents, maxtry=2):
    m, k = len(it_chunks), len(zh_sents)
    if not (it_chunks and zh_sents):
        return None, "fallback"
    msgs = build_prompt(it_chunks, zh_sents)
    for attempt in range(maxtry):
        try:
            text = call_llm(msgs)
        except Exception as e:
            print("    llm err: %r" % (e,))
            return None, "fallback"
        mp = parse_map(text, m, k)
        if mp is not None:
            return mp, "llm"
        if attempt < maxtry - 1:
            msgs = msgs + [{"role": "assistant", "content": text[:1500]},
                           {"role": "user", "content":
                            ("Il JSON non e' valido. Devi restituire SOLO "
                             "{\"map\":[i1,i2,...,i%d]} di lunghezza %d, ogni i_k "
                             "intero 1..%d, NON-DECRESCENTE, e ogni italiano 1..%d "
                             "deve comparire almeno una volta. Rispondi SOLO JSON."
                             ) % (k, k, m, m)}]
    return None, "fallback"


# ----------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------
def build_units(sid, it_chunks, zh_sents, mp):
    """mp: list length k (Chinese sentence -> Italian chunk idx). Build units."""
    m = len(it_chunks)
    zh_by_chunk = {i: [] for i in range(1, m + 1)}
    for sent_idx, chunk_idx in enumerate(mp, 1):
        zh_by_chunk.setdefault(chunk_idx, []).append(zh_sents[sent_idx - 1])
    units = []
    for i, itext in enumerate(it_chunks, 1):
        zh = "\n".join(zh_by_chunk.get(i, []))
        units.append({
            "id": "p%02d" % i,
            "it": itext,
            "zh": zh,
            "audio": "audio/%s/p%02d.mp3" % (sid, i),
        })
    return units


def process_story(f, cache, use_llm=True):
    name = os.path.basename(f)
    m = re.match(r'^(\d+)\.', name)
    sid = m.group(1) if m else name
    ps = P.docx_paras(f)
    if not ps:
        return None
    it_title, zh_title = P.split_title(ps[0])
    if not it_title and sid in P.TITLE_FIX:
        it_title = P.TITLE_FIX[sid]
    body = ps[1:]
    it_raw = [x for x in body if not P.is_zh(x)]
    zh_raw = [x for x in body if P.is_zh(x)]
    # 1) re-segment Italian
    it_sents = []
    for p in it_raw:
        it_sents.extend(split_sentences_it(p))
    it_chunks = resegment(it_sents)
    # 2) split Chinese into sentences
    zh_sents = []
    for p in zh_raw:
        zh_sents.extend(split_sentences_zh(p))
    m_, k = len(it_chunks), len(zh_sents)
    # cached?
    if sid in cache and use_llm:
        c = cache[sid]
        cprev = c.get("map")
        csrc = c.get("src")
        if cprev is not None and isinstance(cprev, list) and len(cprev) == k \
                and all(1 <= x <= m_ for x in cprev) and csrc == "llm":
            units = build_units(sid, it_chunks, zh_sents, cprev)
            return {"id": sid, "title_it": it_title, "title_zh": zh_title,
                    "paras": units, "src": "llm(cached)"}
        if cprev is not None and isinstance(cprev, list) and len(cprev) == k \
                and csrc == "fallback":
            units = build_units(sid, it_chunks, zh_sents, cprev)
            return {"id": sid, "title_it": it_title, "title_zh": zh_title,
                    "paras": units, "src": "fallback(cached)"}
    # compute
    if zh_sents and use_llm:
        mp, src = align_story(it_chunks, zh_sents)
        if mp is None:
            mp = align_sentences_ratio(it_chunks, zh_sents)
            src = "ratio"
    else:
        mp = align_sentences_ratio(it_chunks, zh_sents)
        src = "ratio"
    cache[sid] = {"map": mp, "src": src}
    units = build_units(sid, it_chunks, zh_sents, mp)
    return {"id": sid, "title_it": it_title, "title_zh": zh_title,
            "paras": units, "src": src, "_zhs": k}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default="", help="comma list of story ids to limit")
    ap.add_argument("--nollm", action="store_true",
                    help="skip LLM, use deterministic sentence-level ratio")
    args = ap.parse_args()
    only = set(args.ids.split(",")) if args.ids else None
    use_llm = not args.nollm

    files = sorted(glob.glob(os.path.join(P.SRC, "*.docx")),
                   key=lambda f: int(re.match(r"^(\d+)", os.path.basename(f)).group(1)))
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE, encoding="utf-8"))
        except Exception:
            cache = {}
    stories = []
    cnt = {"llm": 0, "fallback": 0}
    for f in files:
        name = os.path.basename(f)
        m = re.match(r'^(\d+)\.', name)
        sid = m.group(1) if m else name
        if only and sid not in only:
            continue
        st = process_story(f, cache, use_llm=use_llm)
        if st is None:
            continue
        stories.append(st)
        s = st["src"].split("(")[0]
        cnt[s] = cnt.get(s, 0) + 1
        print("  [%s] %s  it_paras=%d zh_sents=%d" % (
            sid, st["src"], len(st["paras"]), st.get("_zhs", 0)))
        json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
        time.sleep(0.3)
    # sort
    stories.sort(key=lambda s: s["id"])
    for s in stories:
        s.pop("_zhs", None)
    meta = {
        "title_it": "Fiabe di Grimm",
        "title_zh": "格林童话",
        "subtitle_it": "Le fiabe dei fratelli Grimm",
        "subtitle_zh": "格林兄弟童话集 · 意中双语",
        "author": "Fratelli Grimm",
        "lang": "it-IT",
        "voice": "it-IT-ElsaNeural",
        "story_count": len(stories),
        "para_count": sum(len(s["paras"]) for s in stories),
        "align": "llm-glm-4-flash (it-resegmented + zh-sentence-aligned)",
    }
    data = {"meta": meta, "stories": stories}
    with open(os.path.join(OUT, "data", "stories.js"), "w", encoding="utf-8") as fh:
        fh.write("window.__GRIMM__ = ")
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write(";\n")
    # manifest for audio
    man = [{"id": s["id"], "n": len(s["paras"]),
            "paras": [{"pid": p["id"], "text": p["it"]} for p in s["paras"]]}
           for s in stories]
    with open(os.path.join(OUT, "build", "audio_manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(man, fh, ensure_ascii=False)
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    print("\nDONE. stories=%d | LLM=%d | fallback=%d | paras=%d" % (
        len(stories), cnt.get("llm", 0), cnt.get("fallback", 0), meta["para_count"]))


if __name__ == "__main__":
    main()
