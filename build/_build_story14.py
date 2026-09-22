# -*- coding: utf-8 -*-
"""Build story 14 (Le tre filatrici / 三个纺纱女) data files, matching the
latest convention of stories 01-13:
- Italian: «» guillemets, NO space before open quote (:« style), balance «==».
- Chinese: full-width "" (U+201C/U+201D), nested '' (U+2018/U+2019),
  NO 「」, NO ASCII straight quotes, NO em-dash ——.
Rebuilds: data/st/14.js (no guard, no src), data/stories.js (replace paras),
data/index.js (recompute para_count), build/audio_manifest.json (replace text).
35 sentences / 10 sections. Multi-sentence quoted speeches are merged into one
para so «» stays balanced per para (same approach as story 13).
"""
import re, json, os

ROOT = r"D:/意大利语材料/grimm-fiabe"
SID = "14"
TITLE_IT = "Le tre filatrici"
TITLE_ZH = "三个纺纱女"

# (it, zh) pairs — one sentence per para (35 paras). Italian uses «»; Chinese
# full-width "" with nested ''; no ASCII/「」/em-dash.
PAIRS = [
("C'era una volta una ragazza che era assai pigra e non voleva filare e la madre poteva dirle quello che voleva, ma non riusciva a convincerla.",
"从前有个姑娘生性极懒，不肯纺纱；母亲怎么说都劝不动她。"),

("Alla fine la madre perse la pazienza e cominciò a picchiarla, tanto che la ragazza cominciò a piangere forte.",
"最后母亲失去耐心，动手打她，姑娘便放声大哭起来。"),

("Allora accadde che la regina passasse proprio di là e udì il pianto, si fermò, entrò nella casa della ragazza e chiese alla madre perché picchiasse sua figlia tanto che si sentivano gli urli fino fuori sulla strada.",
"偏巧王后从那儿路过，听见哭声，就停下脚步，走进姑娘家，问母亲为何打女儿，打得外面街上都听得见喊声。"),

("La donna si vergognò del fatto di dover far sapere quanto sua figlia fosse pigra e disse: «Non riesco a farla smettere di filare, vuole solo e soltanto filare e io sono povera e non riesco a procurarle la canapa».",
"女人不好意思说出女儿有多懒，便说：“我没法让她停下不纺，她只想纺，可我穷，买不起亚麻给她。”"),

("Allora la regina rispose: «La cosa che mi piace di più è il filare e non sono felice se non sento il ronzio della ruota: lascia che tua figlia venga con me al castello, io ho canapa a sufficienza, e può filare fino a che ne ha voglia».",
"王后答道：“我最爱的就是纺纱，听不见纺车嗡嗡响就不快活。让你女儿跟我去王宫吧，我有的是亚麻，她想纺多久就纺多久。”"),

("La madre ne fu felicissima e la regina si portò con sé la figlia.",
"母亲高兴极了，王后便把姑娘带走了。"),

("Appena giunte al castello la accompagnò in tre cameroni, che erano pieni zeppi della più bella canapa.",
"一到王宫，王后就领她去看三间大屋，里面塞满了上好的亚麻。"),

("«Filami questa canapa», disse, «e quando avrai finito diverrai la sposa del mio figlio maggiore. Anche se sei povera, non me ne importa, la tua solerzia è già di per sé una gran dote.»",
"“把这亚麻纺了吧，”王后说，“纺完你就做我长子的新娘。你虽穷，我并不在意，你的勤快本身就是一份厚礼。”"),

("La fanciulla si spaventò molto, perché proprio non avrebbe saputo filare quella canapa nemmeno se avesse filato trecento anni dalla mattina alla sera.",
"姑娘吓坏了，因为她压根不会纺这亚麻，就算从早到晚纺上三百年也不成。"),

("Quando fu sola, cominciò a piangere e così rimase tre giorni senza muovere un dito.",
"独自一人时她就哭，一连三天没动一个指头。"),

("Il terzo giorno la regina venne e quando vide che non era stato filato un bel niente, molto si stupì, ma la fanciulla si scusò dicendo che il grande dispiacere della lontananza dalla casa di sua madre non le avevano permesso d'iniziare.",
"第三天王后来了，见一根线也没纺出来，十分惊讶；姑娘却赔不是说，远离母亲的家令她万分忧伤，所以没能动手。"),

("La regina si lasciò convincere, ma nell'andarsene disse: «Domani devi iniziare a lavorare».",
"王后信了她的话，临走时却说：“明天你得开始干活了。”"),

("Quando la fanciulla fu di nuovo sola, non sapeva più cosa fare e, nella disperazione, si avvicinò alla finestra.",
"姑娘又只剩一个人，不知怎么办才好，绝望中凑到了窗边。"),

("Così vide arrivare tre donne, la prima aveva un piede piatto, la seconda il labbro inferiore tanto grosso che le pendeva sopra il mento, e la terza aveva un gran pollicione.",
"她看见三个女人走来：第一个脚掌扁平，第二个下嘴唇厚得出奇，耷拉到下巴上，第三个长了个大拇趾。"),

("Se ne stettero ferme davanti alla finestra, guardarono dentro e chiesero alla fanciulla cosa le mancasse.",
"她们在窗前站定，朝里张望，问姑娘缺些什么。"),

("Lei raccontò la sua pena, loro le offrirono aiuto e dissero: «Se ci inviterai a nozze e non ti vergognerai di noi e ci chiamerai come madrine e ci farai sedere al tuo tavolo, noi fileremo la tua canapa e anche in fretta».",
"姑娘说出了自己的苦衷，她们便答应帮忙，说：“只要你请我们赴宴，不嫌弃我们，认我们做教母，让我们上你的席，我们就把你的亚麻纺完，而且纺得飞快。”"),

("«Volentierissimo», disse la ragazza, «entrate e iniziate subito il lavoro.»",
"“太乐意了，”姑娘说，“进来吧，立刻开工。”"),

("Così fece entrare le tre strane donne e fece loro uno spazio nella prima camera in modo che potessero sedere e cominciare a filare.",
"于是她让三个古怪的女人进屋，在第一间屋里给她们腾出地方坐下纺纱。"),

("La prima prendeva il filo e faceva muovere la ruota, la seconda lo inumidiva, la terza lo torceva e batteva col pollice sul tavolo e ogni volta che batteva cadeva a terra una matassina filata in maniera meravigliosa.",
"第一个抽下线来转动纺车，第二个把线润湿，第三个把线拧成股，还用大拇指在桌上敲；每敲一下，就有一绞纺得极漂亮的线落到地上。"),

("Davanti alla regina nascose le tre filatrici e mostrò, ogni volta che venne a controllare, la quantità di canapa filata e le lodi di lei erano senza fine.",
"姑娘把三个纺纱女藏起来不让王后看见，王后每次来查看，她都把纺好的亚麻亮出来，王后赞不绝口。"),

("Quando la prima stanza fu vuota, entrò nella seconda e poi nella terza e anche questa fu presto terminata.",
"第一间屋空了，她又进第二间，接着是第三间，很快也纺完了。"),

("Allora le tre donne presero commiato e dissero alla fanciulla: «Non scordarti quello che hai promesso e ne verrà la tua fortuna».",
"于是三个女人告辞，对姑娘说：“别忘了你许下的诺言，好运就会落到你头上。”"),

("Quando la fanciulla mostrò alla regina le stanze vuote e il grande mucchio di canapa filata, si prepararono le nozze e lo sposo si rallegrò di avere una moglie così diligente e saggia e molto la lodò.",
"姑娘把空屋和堆成小山的亚麻指给王后看，婚事便筹备起来；新郎为自己娶了这样勤快又明理的妻子而高兴，把她夸个不停。"),

("«Io ho tre madrine», disse la fanciulla, «e poiché mi hanno fatto molto del bene, non le vorrei dimenticare nel momento della mia gioia. Permettimi di invitarle a nozze e di farle sedere con noi.»",
"“我有三位教母，”姑娘说，“她们待我这样好，我高兴的时候可不能把她们忘了。请让我请她们来赴宴，让她们和我们一起坐席。”"),

("La regina e lo sposo concessero il permesso.",
"王后和新郎都答应了。"),

("Quando iniziò la festa entrarono le tre donne con costumi meravigliosi e la sposa disse: «Benvenute, care madrine».",
"宴会一开始，三个女人盛装进来，新娘说：“欢迎你们，亲爱的教母。”"),

("«Ah», disse lo sposo, «come hai fatto la loro conoscenza?»",
"“啊，”新郎说，“你是怎么结识她们的？”"),

("Poi si avvicinò a quella col largo piede piatto e le chiese: «Come mai avete un piede così largo?».",
"接着他走到那个扁平大脚的女人身前，问：“您的脚怎么这么宽？”"),

("«A forza di pestare sull'arcolaio», disse, «a forza di pestare.»",
"“踩纺车踩的，”女人说，“踩出来的。”"),

("Poi lo sposo andò dalla seconda e chiese: «Perché avete un labbro che pende?».",
"新郎又走到第二个女人身前，问：“您的嘴唇怎么耷拉着？”"),

("«A forza di inumidire il filo, a forza inumidire», disse la seconda.",
"“润线润的，”第二个说，“润线润的。”"),

("Poi chiese alla terza: «Perché avete un pollice così grande?».",
"他又问第三个：“您的拇指怎么这么大？”"),

("«A forza di torcere il filo», rispose questa, «a forza di torcere il filo.»",
"“拧线拧的，”这女人答道，“拧线拧的。”"),

("Allora il principe si spaventò e disse: «D'ora in poi la mia bella sposa non dovrà più toccare una rocca per filare».",
"王子吓了一跳，说：“从今往后，我美丽的妻子再也不必碰纺车了。”"),

("E fu così che questa si liberò dall'odiato filare.",
"就这样，她摆脱了那可恨的纺纱活儿。"),
]

# SEC grouping by narrative section (10 sections, 35 paras total)
SEC = ([1]*3 + [2]*3 + [3]*2 + [4]*4 + [5]*4 + [6]*4 + [7]*2 + [8]*4 + [9]*7 + [10]*2)
assert len(PAIRS) == len(SEC), (len(PAIRS), len(SEC))


def clean_it(s):
    s = s.replace("\uFFFC", " ")          # drop object-replacement artifact
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

    # 1) data/st/14.js  (NO guard, NO src — match 11/12/13.js)
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
