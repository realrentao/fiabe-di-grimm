# -*- coding: utf-8 -*-
"""Build story 17 (La serpe bianca / 白蛇) data files, matching the latest
convention of stories 01-16:
- Italian: «» guillemets, NO space before open quote (:« style), balance «==».
  IT dialogue-attribution uses :« style (no em-dash needed here).
- Chinese: full-width "" (U+201C/U+201D), nested '' (U+2018/U+2019),
  NO 「」, NO ASCII straight quotes, NO em-dash ——.
Rebuilds: data/st/17.js (no guard, no src), data/stories.js (replace paras),
data/index.js (recompute para_count), build/audio_manifest.json (replace text).
43 sentences / 5 sections. Re-segmented from the user's authoritative Italian
text (legacy 17.js used an incompatible older translation).
"""
import re, json, os

ROOT = r"D:/意大利语材料/grimm-fiabe"
SID = "17"
TITLE_IT = "La serpe bianca"
TITLE_ZH = "白蛇"

# (it, zh) pairs — one sentence per para (43 paras). Italian uses «»; Chinese
# full-width "" with nested ''; no ASCII/「」/em-dash. Attribution :« style.
PAIRS = [
# SEC1 — il piatto coperto e la scoperta della serpe bianca
("C'era una volta un re potente e saggio che ogni giorno, a pranzo, quando la tavola era sparecchiata e non c'era più nessuno, si faceva portare, da uno dei servi più fedeli, ancora un piatto, coperto.",
"从前有位强大而明智的国王，每天用过饭、桌子已经收拾干净、旁人也都退下之后，便叫一名最忠实的侍从再给他端上一道盖着的菜。"),

("Solamente lui ne mangiava, poi lo richiudeva, e nessuno sapeva che cosa vi fosse dentro.",
"只有他一个人吃，吃完又盖起来，谁也不知道里面究竟是什么。"),

("Un giorno avvenne che il servo, quando il re gli diede il piatto da portare via, non seppe resistere alla tentazione, lo portò nella propria camera, lo aprì e vi trovò dentro una serpe bianca.",
"有一天，国王把那盘子交给他端走，侍从却经不住诱惑，把它端回自己屋里，揭开一看，里面竟是一条白蛇。"),

("Vedendola gli venne una tale voglia di mangiarne che non potè trattenersi: ne tagliò un pezzetto e se lo mangiò.",
"他见了，馋得忍不住，便割下一小块送进嘴里。"),

("Ma appena lo sfiorò con la lingua, udì con chiarezza ciò che si dicevano i passeri e gli altri uccelli davanti alla finestra e comprese così che capiva il linguaggio degli animali.",
"可蛇肉刚碰到舌头，他就清清楚楚听见窗前麻雀和其他鸟儿在说些什么，这才明白自己听懂了兽语。"),

# SEC2 — l'anello smarrito e l'anatra
("Ora avvenne che proprio quel giorno la regina smarrì uno dei suoi anelli più belli, e il sospetto cadde su quel servo.",
"偏巧就在这天，王后丢了一枚最漂亮的戒指，嫌疑便落到了这侍从头上。"),

("Il re lo rimproverò aspramente e minacciò di condannarlo, se entro quel giorno non avesse indicato il malfattore.",
"国王把他狠狠训斥一顿，并威胁说：若当天指不出真凶，就要治他的罪。"),

("Allora il servo si spaventò e non sapeva cosa fare.",
"侍从吓坏了，不知如何是好。"),

("Nella sua inquietudine, scese in cortile: là, vicino a un ruscello, le anatre riposavano tranquille e si facevano le loro confidenze.",
"他心烦意乱，走下院子；只见小溪边几只鸭子安安静静歇着，正说着各自的悄悄话。"),

("Egli ne sentì una che diceva: «Che peso ho sullo stomaco! Nella fretta ho ingoiato un anello che era sotto la finestra della regina».",
"他听见其中一只说：“我肚子沉得慌！匆忙间我把王后窗下那枚戒指吞下去了。”"),

("Subito il servo l'afferrò per il collo, la portò al cuoco e disse: «Ammazza prima questa, è ben pasciuta».",
"侍从立刻掐住它的脖子，拎到厨子那里说：“先把这只宰了，它养得挺肥。”"),

("Il cuoco le tagliò il collo e quando fu sbuzzata le trovò nello stomaco l'anello della regina.",
"厨子一刀割了它的脖子，剖开肚子，竟在里头找到了王后的戒指。"),

("Il servo lo portò al re che se ne rallegrò molto, e volendo riparare al proprio errore gli disse: «Chiedi ciò che vuoi, e dì quale carica desideri a corte».",
"侍从把戒指献给国王，国王十分高兴，想弥补自己的过错，便说：“你要什么尽管说，想在宫里担什么职位也行。”"),

("Ma il servo rifiutò ogni cosa e chiese soltanto un cavallo e del denaro per il viaggio, poiché desiderava girare il mondo.",
"可侍从什么也不要，只求一匹马和一点盘缠，因为他想出门去见见世面。"),

# SEC3 — il viaggio e gli animali salvati (pesci, formiche, corvi)
("Così se ne andò a cavallo e giunse presso uno stagno dove tre pesci si erano impigliati nelle canne e boccheggiavano fuor d'acqua, lamentandosi di dover morire così miseramente.",
"于是他骑马上路，来到一个池塘边，见三条鱼卡在芦苇里，在岸上张着嘴挣扎，哀叹自己要这样凄惨地死掉。"),

("Egli capì le loro parole e ne ebbe pietà, così scese da cavallo e li rimise in acqua.",
"他听懂了它们的话，心生怜悯，便下马把它们放回水中。"),

("Allora i pesci gridarono: «Ce ne ricorderemo e ti ricompenseremo!».",
"鱼儿们喊道：“我们记着你的好处，一定会报答你！”"),

("Egli proseguì e poco dopo udì, ai suoi piedi, un re delle formiche che diceva: «Se l'uomo girasse al largo con la sua bestia! Mi calpesta tante di quelle formiche!».",
"他继续赶路，不一会儿听见脚边蚂蚁王叫道：“这人快带着他的牲口绕开吧！他踩死我多少蚂蚁啊！”"),

("Egli guardò a terra e vide che il suo cavallo era entrato in un formicaio, allora deviò il cammino e il re delle formiche gridò: «Ce ne ricorderemo e ti ricompenseremo!».",
"他低头一看，自己的马踩进了蚁巢，便绕道避开；蚂蚁王喊道：“我们记着你的好处，一定会报答你！”"),

("Proseguì e giunse in un bosco.",
"他继续走，来到一片树林。"),

("Là due corvi, padre e madre, gettavano i loro piccoli fuori dal nido e dicevano: «Siete grandi a sufficienza per mantenervi da soli, noi non possiamo più sfamarvi!».",
"那儿一对乌鸦夫妻正把雏鸟往外扔，说：“你们够大了，该自己觅食，我们再也养不活你们了！”"),

("I piccoli giacevano a terra, sbattevano le loro piccole alucce e gridavano: «Come possiamo mantenerci da soli! Non sappiamo ancora volare per procacciarci il cibo! Siamo costretti a morire di fame!».",
"小乌鸦趴在地上拍着小翅膀叫：“我们怎么养活自己！还不会飞，哪去找吃的！非要饿死不可了！”"),

("Egli scese a terra, uccise il suo cavallo con la spada e lo diede in pasto ai piccoli corvi.",
"他下了马，一剑杀死自己的马，喂给小乌鸦们吃。"),

("Questi si avvicinarono saltellando, si saziarono e dissero: «Ce ne ricorderemo e ti ricompenseremo».",
"小乌鸦蹦跳着围上来，吃饱后说：“我们记着你的好处，一定会报答你。”"),

# SEC4 — la principessa e la prova dell'anello
("Ora egli proseguì a piedi e, cammina cammina, giunse in una grande città.",
"他步行继续走，走啊走，来到一座大城。"),

("Un uomo a cavallo andava dicendo che colui che voleva diventare sposo della giovane principessa doveva eseguire un compito che ella gli avrebbe assegnato; ma chi provava e non lo portava a termine, avrebbe perso la vita.",
"有个骑马的人沿街喊：谁想当年轻公主的丈夫，须完成她交给的任务；可谁去试而没做成，就得送命。"),

("Nessuno voleva presentarsi, perché già tanti ci avevano rimesso la vita.",
"没人敢去应征，因为已有许多人因此丢了性命。"),

("Il giovane pensò: «Che ho da perdere? Tentiamo!».",
"年轻人想：“我有什么可输的？试试看！”"),

("Così andò davanti al re e a sua figlia e si annunciò come pretendente.",
"于是他来到国王和公主面前，自报要当求婚者。"),

("Allora lo condussero in riva al mare; gettarono un anello in acqua e gli ordinarono di ripescarlo.",
"人们把他带到海边，把一枚戒指丢进海里，命他捞上来。"),

("Gli dissero inoltre che se si tuffava e ritornava a galla senza l'anello, lo avrebbero ributtato giù per farlo morire.",
"他们还说，若他跳下去没了戒指浮上来，就再把人扔下去淹死。"),

("Poi fu lasciato solo, e mentre si trovava sulla riva e pensava che cosa mai potesse fare per prendere l'anello, vide avvicinarsi i tre pesci che egli aveva salvato dalle canne e rimesso in acqua.",
"随后只剩他一人；他站在岸边，正想着怎么才能拿到戒指，忽然看见自己救过、放回水里的那三条鱼游了过来。"),

("Quello di mezzo aveva in bocca una conchiglia, che depose sulla riva, ai piedi del giovane; e quando egli l'aprì ci trovò dentro l'anello.",
"中间那条嘴里衔着一只贝壳，放在年轻人脚边的岸上；他打开一看，戒指就在里面。"),

("Pieno di gioia lo portò al re e chiese sua figlia in sposa.",
"他满心欢喜地把戒指献给国王，请求娶公主为妻。"),

# SEC5 — miglio, mela e finale
("Ma questa, quando udì che lui non era un principe, non lo volle.",
"可公主听说他不是王子，便不肯嫁。"),

("Uscì in giardino, rovesciò dieci sacchi pieni di miglio sull'erba e disse: «Dovrà raccoglierlo per domattina, prima che sorga il sole; e che non ne manchi neanche un granello!».",
"她走到园子里，把十袋小米倒在地上，说：“明早日出前他得把米收好，一粒也不能少！”"),

("Il giovane non sarebbe riuscito a portare a termine il compito se i fedeli animali non lo avessero aiutato.",
"若没有那些知恩的动物帮忙，年轻人根本完不成这任务。"),

("Di notte venne il re delle formiche e, con le sue mille e mille formiche raccolse tutto il miglio, lo ammucchiò nei sacchi e, prima che sorgesse il sole del mattino successivo, aveva finito il lavoro senza che neanche un granello andasse perduto.",
"夜里蚂蚁王带着成千上万只蚂蚁来，把小米一粒不落地全收进袋里；第二天日出前，活儿就干完了。"),

("Quando la principessa venne in giardino e vide tutto ciò, si meravigliò e disse: «Anche se ha eseguito pure questo compito, ed è giovane e bello, non lo sposerò se prima non mi avrà portato una mela dall'albero della vita».",
"公主来到园中见此情景，十分惊讶，说：“即便这关他也过了，人又年轻又俊，可若他不能从生命树上摘来苹果，我还是不嫁。”"),

("Ma i corvi che erano stati cacciati dal nido e che egli aveva nutrito, erano cresciuti e avevano udito quello che voleva la principessa.",
"可那些被赶出巢、由他喂大的乌鸦已经长大，听见了公主的要求。"),

("Volarono via e ben presto uno di loro ritornò portando una mela nel becco e la lasciò cadere fra le mani del giovane.",
"它们飞走了，不久其中一只衔着一只苹果回来，落在年轻人手里。"),

("Quando questi la portò alla principessa ella lo accettò con gioia e divenne sua sposa.",
"年轻人把苹果献给公主，公主高兴地应允，成了他的新娘。"),

("Alla morte del vecchio re, il principe ne ereditò la corona.",
"老国王去世，这位王子继承了王冠。"),
]

# SEC grouping by narrative section (5 sections, 43 paras total)
SEC = ([1]*5 + [2]*9 + [3]*10 + [4]*10 + [5]*9)
assert len(PAIRS) == len(SEC), (len(PAIRS), len(SEC))


def clean_it(s):
    s = s.replace(" ", " ")          # drop object-replacement artifact
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s+([«»,.!?:;])", r"\1", s)        # no space before these
    s = re.sub(r"([,:;])(?![ «»])", r"\1 ", s)      # space after ,:; unless before quote
    s = re.sub(r" +", " ", s)
    return s.strip()


def fix_zh(zh):
    """Convert ASCII straight quotes (from escaped \" in source) to full-width
    “ ” alternating open/close. Nested ' ' (U+2018/U+2019) are left intact.
    If no ASCII quotes present, returns unchanged."""
    if '"' not in zh:
        return zh
    out = []
    open_q = True
    n = 0
    for ch in zh:
        if ch == '"':
            out.append("“" if open_q else "”")
            open_q = not open_q
            n += 1
        else:
            out.append(ch)
    assert n % 2 == 0, "odd ASCII quotes in zh: %r" % zh
    return "".join(out)


def build_paras():
    paras = []
    for i, (it, zh) in enumerate(PAIRS, start=1):
        pid = "s%03d" % i
        paras.append({
            "pid": pid,
            "sec": SEC[i - 1],
            "it": clean_it(it),
            "zh": fix_zh(zh),
            "audio": "audio/%s/%s.mp3" % (SID, pid),
            "audio_zh": "audio/%s/%s.mp3" % (SID, "z%03d" % i),
        })
    return paras


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def main():
    paras = build_paras()

    # 1) data/st/17.js  (NO guard, NO src — match 11-16.js)
    st_obj = {"id": SID, "title_it": TITLE_IT, "title_zh": TITLE_ZH, "paras": paras}
    with open(os.path.join(ROOT, "data", "st", SID + ".js"), "w", encoding="utf-8") as f:
        f.write("window.__GRIMM_STORIES__['%s'] = %s;" % (SID, dump(st_obj)))

    # 2) data/stories.js  (replace paras by id, no src)
    t = open(os.path.join(ROOT, "data", "stories.js"), encoding="utf-8").read()
    m = re.search(r"window\.__GRIMM__ = (\{.*\});\s*$", t, re.S)
    root = json.loads(m.group(1))
    repl = {"id": SID, "title_it": TITLE_IT, "title_zh": TITLE_ZH, "paras": paras}
    found = False
    for idx, st in enumerate(root["stories"]):
        if st["id"] == SID:
            root["stories"][idx] = repl
            found = True
            break
    if not found:
        root["stories"].append(repl)
    with open(os.path.join(ROOT, "data", "stories.js"), "w", encoding="utf-8") as f:
        f.write("window.__GRIMM__ = %s;" % dump(root))

    # 3) data/index.js  (recompute para_count)
    t = open(os.path.join(ROOT, "data", "index.js"), encoding="utf-8").read()
    m = re.search(r"window\.__GRIMM_INDEX__ = (\{.*\});\s*$", t, re.S)
    idx_root = json.loads(m.group(1))
    para_count = sum(len(s["paras"]) for s in root["stories"])
    idx_root["meta"]["para_count"] = para_count
    with open(os.path.join(ROOT, "data", "index.js"), "w", encoding="utf-8") as f:
        f.write("window.__GRIMM_INDEX__ = %s;" % dump(idx_root))

    # 4) build/audio_manifest.json  (replace text by id)
    man = json.load(open(os.path.join(ROOT, "build", "audio_manifest.json"), encoding="utf-8"))
    man_entry = {"id": SID, "paras": [{"pid": p["pid"], "text": p["it"]} for p in paras]}
    mf = False
    for i2, e in enumerate(man):
        if e["id"] == SID:
            man[i2] = man_entry
            mf = True
            break
    if not mf:
        man.append(man_entry)
    with open(os.path.join(ROOT, "build", "audio_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, separators=(",", ":"))

    print("paras=%d sec=%d para_count=%d" % (len(paras), len(set(SEC)), para_count))


if __name__ == "__main__":
    main()
