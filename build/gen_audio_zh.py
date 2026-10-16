# -*- coding: utf-8 -*-
"""Generate Chinese TTS audio for stories 01 & 02 via edge-tts.
One mp3 per sentence: audio/<id>/zNNN.mp3  (Chinese voice).
Text source: para["zh"]; output filename from para["audio_zh"].
Resume-safe (skips existing >200 bytes).
"""
import asyncio, json, os, re, io, time
import edge_tts

OUT = r"D:/意大利语材料/grimm-fiabe"
VOICE = "zh-CN-XiaoxiaoNeural"
IDS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "70", "71", "72", "73", "74", "75", "76", "77", "78", "79", "80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99", "100", "101", "102", "103", "104", "105", "106", "107", "108", "109", "110", "111", "112", "113", "114", "115", "116", "117", "118", "119", "120", "121", "122", "123", "124", "125", "126", "127", "128", "129", "141", "142", "143", "144", "145", "146", "147", "148", "149", "150", "151", "152", "153", "154", "155", "156", "157", "158", "159", "160", "161", "162", "163", "164", "165", "166", "167", "168", "169", "170", "171", "172", "173", "174", "175", "176", "177", "178", "179", "180", "181", "182", "183", "184", "185", "186", "187", "188", "189", "190", "191", "192", "193", "194", "195", "196", "197", "198", "199", "200", "201"]
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
    # poem line-breaks written as "/ " must be a PAUSE, not pronounced
    # (story 19's Chinese rhyme uses "，/ " -> keep the preceding comma as the pause)
    text = text.replace("/ ", "")
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
                await asyncio.wait_for(comm.save(path), timeout=45)
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
