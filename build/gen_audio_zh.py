# -*- coding: utf-8 -*-
"""Generate Chinese TTS audio for stories 01 & 02 via edge-tts.
One mp3 per sentence: audio/<id>/zNNN.mp3  (Chinese voice).
Text source: para["zh"]; output filename from para["audio_zh"].
Resume-safe (skips existing >200 bytes).
"""
import asyncio, json, os, re, io, time
import edge_tts

OUT = r"D:/workbuddy工作区/2026-08-23-21-28-02/grimm-fiabe"
VOICE = "zh-CN-XiaoxiaoNeural"
IDS = ["01", "02", "03", "04", "05", "06", "07", "08"]
CONCURRENCY = 12
LOG = os.path.join(OUT, "build", "audio_zh_gen.log")

done = 0
total = 0
lock = asyncio.Lock()
start = time.time()


def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_paras(sid):
    fn = os.path.join(OUT, "data", "st", sid + ".js")
    t = io.open(fn, encoding="utf-8").read()
    m = re.search(r"window\.__GRIMM_STORIES__\['" + sid + r"'\] = (\{.*\});\s*$", t, re.S)
    return json.loads(m.group(1))["paras"]


async def gen_one(sem, sid, para):
    global done
    fname = para.get("audio_zh", "").split("/")[-1]
    if not fname:
        async with lock:
            done += 1
        return
    path = os.path.join(OUT, "audio", sid, fname)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = (para.get("zh") or "").strip()
    if not text:
        async with lock:
            done += 1
        return
    if os.path.exists(path) and os.path.getsize(path) > 200:
        async with lock:
            done += 1
        return
    async with sem:
        for attempt in range(4):
            try:
                comm = edge_tts.Communicate(text, VOICE)
                await comm.save(path)
                if os.path.getsize(path) > 200:
                    break
            except Exception as e:
                await asyncio.sleep(1.5 * (attempt + 1))
    async with lock:
        done += 1
        if done % 20 == 0 or done == total:
            log(f"progress {done}/{total}  ({done*100//max(total,1)}%)  t={int(time.time()-start)}s")


async def main():
    global total
    items = []
    for sid in IDS:
        for p in load_paras(sid):
            items.append((sid, p))
    total = len(items)
    existing = 0
    for sid, p in items:
        fn = p.get("audio_zh", "").split("/")[-1]
        if fn and os.path.exists(os.path.join(OUT, "audio", sid, fn)):
            existing += 1
    log(f"TOTAL={total} | on disk={existing} | to generate={total-existing}")
    sem = asyncio.Semaphore(CONCURRENCY)
    await asyncio.gather(*[gen_one(sem, sid, p) for sid, p in items])
    log(f"ALL DONE {done}/{total}  total_time={int(time.time()-start)}s")


if __name__ == "__main__":
    asyncio.run(main())
