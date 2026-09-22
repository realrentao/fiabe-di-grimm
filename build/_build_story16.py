# -*- coding: utf-8 -*-
"""Build story 16 (Le tre foglie della serpe / 蛇的三片叶子) data files, matching
the latest convention of stories 01-15:
- Italian: «» guillemets, NO space before open quote (:« style), balance «==».
  IT dialogue-attribution dashes use em-dash «—».
- Chinese: full-width "" (U+201C/U+201D), nested '' (U+2018/U+2019),
  NO 「」, NO ASCII straight quotes, NO em-dash ——.
Rebuilds: data/st/16.js (no guard, no src), data/stories.js (replace paras),
data/index.js (recompute para_count), build/audio_manifest.json (replace text).
52 sentences / 8 sections. The queen's long speech spanning two source sentences
(«Torniamo a casa... ti nominerà erede della corona») is merged into one para so
«» stays balanced per para.
"""
import re, json, os

ROOT = r"D:/意大利语材料/grimm-fiabe"
SID = "16"
TITLE_IT = "Le tre foglie della serpe"
TITLE_ZH = "蛇的三片叶子"

# (it, zh) pairs — one sentence per para (52 paras). Italian uses «»; Chinese
# full-width "" with nested ''; no ASCII/「」/em-dash. Attribution em-dashes «—».
PAIRS = [
# SEC1 — partenza del figlio
("C'era una volta un povero uomo che non ce la faceva più a dar da mangiare al suo unico figlio.",
"从前有个穷苦人，再也没法养活他独生的儿子。"),

("Allora il figlio gli disse: «Caro padre, voi vivete tanto miseramente che io vi sono di peso, preferisco andarmene a vedere se riesco a guadagnarmi il pane».",
"于是儿子对他说：“亲爱的父亲，您过得这样苦，我成了您的累赘，我宁愿出去闯闯，看能不能挣口饭吃。”"),

("Il padre lo benedisse e con grandi lacrime prese commiato da lui.",
"父亲为他祝福，含泪与他道别。"),

# SEC2 — guerra ed eroismo
("In quel tempo il re d'un potente paese faceva la guerra: il giovane prese servizio presso di lui e andò in guerra.",
"那时有个强国的国王正在打仗：年轻人去他手下当了兵，上了战场。"),

("Quando si trovò davanti ai nemici in piena battaglia il rischio era grande, e piovevano le pallottole, tanto che da ogni parte cadevano i suoi compagni.",
"当他在激战中面对敌人，危险很大，子弹像雨点般飞来，同伴们纷纷倒下。"),

("Quando anche il comandante cadde, i superstiti volevano fuggire, ma il giovane si fece avanti, li incoraggiò e disse: «Non lasceremo perire la nostra patria!».",
"连指挥官也阵亡了，幸存者想逃，可年轻人挺身而出，鼓舞大家说：“我们绝不让祖国灭亡！”"),

("Allora gli altri lo seguirono ed egli si aprì una breccia fra i nemici e li sconfisse.",
"于是众人跟着他，他在敌军中杀开一条血路，把他们打垮了。"),

("Quando il re udì che solo a lui si doveva la vittoria, lo elevò sopra gli altri, gli diede molti tesori e ne fece il primo del suo regno.",
"国王听说胜利全靠他一人，便把他擢升众人之上，赏了许多珍宝，立他为王国第一人。"),

# SEC3 — la principessa e il voto
("Il re aveva una figlia, che era molto bella, ma anche molto strana.",
"国王有个女儿，长得非常美，却也十分怪异。"),

("Aveva fatto voto di sposare soltanto chi le avesse promesso che, se lei fosse morta prima, si sarebbe fatto seppellire assieme a lei.",
"她发过誓，只嫁给肯承诺'她若先死，便随她一同下葬'的人。"),

("«Se mi ama davvero», diceva, «a che gli servirebbe ancora la vita!»",
"“他若真爱我，”她说，“活着还有什么意思！”"),

("E anche lei si riprometteva di fare lo stesso e se fosse stato lui a morire prima, lo avrebbe seguito nella tomba.",
"她自己也立下同样的誓：若他先死，便随他入坟。"),

("Questo strano voto le aveva tenuto lontano tutti i pretendenti, ma il giovane era talmente affascinato dalla sua bellezza che non badò a nulla e la chiese in moglie a suo padre.",
"这古怪的誓言把求婚者都吓跑了，可年轻人被她的美貌迷住，什么也不顾，向她父亲求了婚。"),

# SEC4 — la proposta e le nozze
("«Ma lo sai — disse il re — cosa devi promettere?»",
"“你可知道，”国王说，“你得承诺什么？”"),

("«Certo, che devo scender con lei nella tomba — rispose il giovane — ma il mio amore è tanto grande che non mi preoccupo del pericolo.»",
"“我当然得随她下墓，”年轻人答道，“可我的爱那样深，全不把危险放在心上。”"),

("Allora il re diede il consenso e le nozze furono celebrate con grande sfarzo.",
"国王便应允了，婚礼办得极尽奢华。"),

("Per un certo tempo vissero felici e contenti, ma accadde che la giovane regina s'ammalò d'una grave malattia e nessun medico fu in grado d'aiutarla.",
"有一阵子他们过得美满，可年轻的王后染上重病，没有一个医生能治好她。"),

# SEC5 — morte della regina e sepoltura
("E quando giacque morta, il giovane re ricordò quello che aveva dovuto promettere, e inorridì al pensiero di scendere con lei nella tomba, ma non c'era scampo: il vecchio re aveva chiuso tutte le porte in modo che non potesse sfuggire al suo destino.",
"等她咽了气，年轻的国王想起自己许过的诺言，一想到要随她下墓就不寒而栗，可无路可逃：老国王锁上了所有的门，叫他逃不掉注定的命运。"),

("Quando giunse il giorno nel quale la salma doveva essere tumulata nella tomba reale, anch'egli fu condotto giù e poi chiusero e sprangarono la porta.",
"到了王后遗体入皇家墓穴那天，他也被人带下去，随后门被关上、闩死。"),

("Accanto alla bara c'era un tavolino con quattro candelieri, quattro pani e quattro bottiglie di vino.",
"棺材旁有张小桌，上面四只烛台、四个面包、四瓶酒。"),

("Quando queste provviste fossero arrivate alla fine, lui avrebbe dovuto morire di fame.",
"等这些给养耗尽，他就要饿死在里面。"),

("Egli se ne stava seduto triste e in grande affanno: mangiava solo un bocconcino di pane al giorno e beveva un gocciolino di vino, eppure vedeva la morte avvicinarsi sempre più.",
"他愁苦地坐着：每天只啃一小口面包、抿一小口酒，却眼看着死神一步步逼近。"),

# SEC6 — la serpe e la resurrezione
("Mentre se ne stava lì con gli occhi fissi davanti a sé, nell'angolo delle arcate della cripta, vide strisciar fuori una serpe che si avvicinava al cadavere della moglie.",
"他正呆坐着，眼睛直直地盯着前方，忽见墓穴拱角处爬出一条蛇，朝妻子的尸身游去。"),

("E poiché egli pensava venisse a morderla, trasse la spada e disse: «Finché vivo non la toccherai», e tagliò la serpe in tre pezzi.",
"他以为蛇要咬她，便拔出剑说：“只要我活着，就由不得你碰她，”把蛇砍成三截。"),

("Poco dopo dall'angolo strisciò fuori un'altra serpe e quando vide la sua compagna morta e fatta a pezzi, se ne andò subito e tornò con tre foglie verdi in bocca.",
"不多时，角里又爬出一条蛇；它见同伴死了、被剁碎，立刻离去，衔着三片绿叶回来。"),

("Prese i tre pezzi della serpe, li riunì con ordine, e mise una foglia verde su ogni ferita.",
"它把蛇的三截捡起、依次拼好，在每处伤口上放一片绿叶。"),

("Subito i pezzi si ricongiunsero, la serpe si mosse e riprese vita, e tutte e due corsero via.",
"伤口立刻接合，蛇动了动，活了过来，两条一起溜走。"),

("Le foglie rimasero per terra e il povero infelice che aveva visto tutto, si domandò se il meraviglioso potere delle foglie che avevano resuscitato la serpe, non avrebbe potuto giovare anche a una creatura umana.",
"叶子留在地上；这可怜人把一切看在眼里，琢磨着：叶子既能救活蛇，说不定也能救活人。"),

("Raccolse le foglie e ne posò una sulla bocca della morta, e le altre due, una per occhio.",
"他捡起叶子，一片放在死者嘴上，另两片各放一只眼睛。"),

("Appena l'ebbe fatto, il sangue riprese a fluire nelle vene di lei, salì fino al pallido viso e gli ridiede colore.",
"刚一放好，血便在她血管里重新流动，涌上苍白的脸，恢复了血色。"),

("Allora ella respirò, aprì gli occhi e disse: «Oh Dio, dove sono!».",
"她于是喘了气，睁开眼说：“天哪，我在哪儿！”"),

("«Sei con me, cara moglie», rispose e le raccontò l'accaduto e come fosse riuscito a riportarla in vita.",
"“你在我身边呢，亲爱的妻子，”他答道，把经过和怎样把她救活说给她听。"),

("Poi le porse un po' di pane e vino e quando lei riprese le forze, andarono entrambi alla porta e gridarono così forte che le guardie li sentirono e avvisarono il re.",
"他递给她些面包和酒；等她缓过力气，两人走到门前，拼命呼喊，卫兵听见了，去禀报国王。"),

("Il re stesso scese e aprì la porta.",
"国王亲自下来，开了门。"),

("Li trovò entrambi freschi e sani e insieme si rallegrarono che ogni dolore fosse passato.",
"见两人都好好的，大家一同欢喜，所有痛苦都过去了。"),

# SEC7 — il tradimento
("Le tre foglie della serpe il giovane re le portò con sé, le diede a un fedele servo e disse: «Conservale con cura e portale sempre con te, chissà in quale occasione ci potranno ancora servire».",
"年轻的国王把蛇的三片叶子带在身上，交给一个忠仆说：“妥善收好，随身带着，说不定哪天还能派上用场。”"),

("Ma nella donna, dopo la resurrezione, era avvenuto un gran cambiamento: era come se dal cuore le fosse svanito l'amore che aveva per suo marito.",
"可这女人复活之后，起了极大的变化：仿佛对丈夫的爱已从心里消失。"),

("Dopo un certo tempo egli volle recarsi per mare a trovare il suo vecchio padre e quando s'imbarcarono sulla nave, dimentica del grande amore e della fedeltà che lui le aveva dimostrato e che l'avevano salvata dalla morte, fu presa da una perversa passione per il capitano della nave.",
"过了些时候，他想渡海去探望老父亲；上了船，她忘了他那份深爱与忠诚（正是这些把她从死里救回），竟对船长生出邪念。"),

("Lo chiamò a sé, prese il dormiente per la testa e mentre il capitano dovette prenderlo per i piedi e insieme lo gettarono in mare.",
"她把船长唤来，一人托住熟睡丈夫的头，船长托脚，一起把他抛进了海里。"),

("Quando il delitto fu compiuto lei gli disse: «Torniamo a casa e diremo che è morto durante il viaggio. Io tanto ti magnificherò e adulerò davanti a mio padre che darà il consenso per le nozze e ti nominerà erede della corona».",
"恶行得手后，她对船长说：“咱们回家，就说他死在路上了。我会在父亲面前把你捧上天、百般讨好，父亲定会同意婚事，立你为王位继承人。”"),

("Ma il fedele servitore che tutto aveva visto, staccò di nascosto una piccola barchetta dalla nave, ci si mise sopra, andò in cerca del suo padrone e lasciò proseguire il viaggio ai traditori.",
"忠仆把这一切看在眼里，悄悄从大船解下一只小艇，坐上去寻找主人，任那两个叛徒继续航行。"),

("Ripescò il morto e con l'aiuto delle tre foglie della serpe, che sempre aveva con sé e che pose sugli occhi e sulla bocca del suo padrone, lo riportò felicemente in vita.",
"他把死人捞起，用随身带着的蛇的三片叶子，敷在主人眼上和嘴上，把他安然救活。"),

("Entrambi remarono con tutte le forze, giorno e notte, e la piccola barca volava talmente in fretta che giunsero dal vecchio re prima degli altri.",
"两人日夜奋力划桨，小艇快得像飞，竟比其他人先到老国王那里。"),

# SEC8 — il ritorno e la giustizia
("Il re si meravigliò vedendoli arrivare soli e chiese cosa fosse accaduto.",
"国王见只有他们两个回来，十分诧异，问出了什么事。"),

("Quando gli narrarono la crudeltà della figlia, disse: «Non posso credere che abbia agito tanto male, ma la verità si farà strada» e li fece entrare entrambi in una stanza dove rimasero nascosti a tutti.",
"听他们讲完女儿的残暴，国王说：“我难信她竟如此狠毒，可真相终会大白，”把两人藏进一间谁也看不见的屋子。"),

("Poco dopo giunse la grande nave e la donna scellerata si presentò al padre con aria mesta.",
"不久大船到了，那恶毒的女人一脸哀伤地来见父亲。"),

("Egli disse: «Perché torni sola? Dov'è tuo marito?».",
"他问：“你怎独自回来？你丈夫在哪儿？”"),

("«Ah, padre mio», rispose lei, «io torno in gran lutto, mio marito durante il viaggio s'è improvvisamente ammalato ed è morto e se non ci fosse stato questo buon capitano, male mi sarebbe andata; egli è stato presente alla sua morte e tutto vi può narrare.»",
"“啊，我的父亲，”她答道，“我回来戴着重孝：我丈夫途中突然病逝，若不是这位好船长，我早完了；他在一旁送终，一切都能讲给您听。”"),

("Il re disse: «Voglio risuscitare il morto», e aprì la porta e chiamò i due.",
"国王说：“我要让死人活过来，”开了门，把那两人唤出。"),

("Quando la donna vide il marito fu come colpita dal fulmine, si gettò ai suoi piedi e chiese grazia.",
"女人一见丈夫，如遭雷击，扑倒在他脚下求饶。"),

("Il re disse: «Non c'è nessuna grazia, egli era pronto a morire per te, tu invece lo hai ucciso nel sonno e devi avere la pena che ti meriti».",
"国王说：“没得饶，他甘愿为你去死，你却在睡中杀他，该受应得的刑罚。”"),

("Così la gettò con colui che l'aveva aiutata su una nave che faceva acqua e li spinse in mare, dove ben presto furono afferrati dalle onde e colati a picco.",
"于是他把她连同帮凶扔上一只漏水的船，推入海中；很快波浪卷住他们，沉了底。"),
]

# SEC grouping by narrative section (8 sections, 52 paras total)
SEC = ([1]*3 + [2]*5 + [3]*5 + [4]*4 + [5]*5 + [6]*13 + [7]*8 + [8]*9)
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

    # 1) data/st/16.js  (NO guard, NO src — match 11-15.js)
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
