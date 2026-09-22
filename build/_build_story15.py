# -*- coding: utf-8 -*-
"""Build story 15 (Hänsel e Gretel / 韩塞尔与格蕾特) data files, matching the
latest convention of stories 01-14:
- Italian: «» guillemets, NO space before open quote (:« style), balance «==».
  IT dialogue-attribution dashes use em-dash «—» (source used hyphen «-» which
  we normalize to «—» for site consistency).
- Chinese: full-width "" (U+201C/U+201D), nested '' (U+2018/U+2019),
  NO 「」, NO ASCII straight quotes, NO em-dash ——.
Rebuilds: data/st/15.js (no guard, no src), data/stories.js (replace paras),
data/index.js (recompute para_count), build/audio_manifest.json (replace text).
120 sentences / 16 sections. Multi-sentence quoted speeches are merged into one
para so «» stays balanced per para (same approach as stories 11-14).
"""
import re, json, os

ROOT = r"D:/意大利语材料/grimm-fiabe"
SID = "15"
TITLE_IT = "Hänsel e Gretel"
TITLE_ZH = "韩塞尔与格蕾特"

# (it, zh) pairs — one sentence per para (120 paras). Italian uses «»; Chinese
# full-width "" with nested ''; no ASCII/「」/em-dash. Attribution hyphens
# normalized to «—».
PAIRS = [
# SEC1 — la famiglia e la carestia
("Proprio di fronte a un grande bosco abitava un povero taglialegna con la moglie e due figli: il figlio si chiamava Hänsel e la figlia Gretel.",
"在大森林边上，住着一个穷樵夫，带着妻子和两个孩子：儿子叫韩塞尔，女儿叫格蕾特。"),

("Il taglialegna aveva poco da mettere sotto i denti e quando nel paese ci fu una grande carestia, non potè nemmeno più procurare il pane quotidiano.",
"樵夫家底薄，遇上大饥荒，连每天的面包都供不上了。"),

# SEC2 — il primo piano dei genitori
("Una sera, mentre i pensieri lo assalivano e si rigirava nel letto dal dispiacere, disse sospirando alla moglie: «Che ne sarà di noi? Come potremo nutrire i nostri figli se non ne abbiamo più nemmeno per noi?...».",
"一天晚上，他满心愁苦，在床上翻来覆去，叹着气对妻子说：“我们可怎么办？要是连自己都吃不饱，又怎么养得活孩子们？……”"),

("«Senti marito mio — rispose la moglie — domattina all'alba li condurremo nel bosco più fitto: accendiamo un fuoco e diamo a ciascuno di loro un pezzetto di pane, poi andiamo al lavoro e li lasciamo lì da soli. Non troveranno più la strada di casa e noi ce ne saremo liberati.»",
"“听我说，我的丈夫，”妻子答道，“明天天一亮，我们就把他们带进最密的树林：生一堆火，给每人一小块面包，然后我们去干活，把他们留在那儿。他们就找不到回家的路了，我们也算甩掉了包袱。”"),

("«No, moglie mia», disse l'uomo, «non lo farò, come potrei avere il coraggio di lasciare i miei figli soli nel bosco? Verrebbero certamente le bestie feroci e subito se li divorerebbero.»",
"“不，我的妻子，”男人说，“我不会这么干的，我哪忍心把孩子们孤零零扔在林子里？野兽准会扑上来把他们吞掉。”"),

("«Sei proprio pazzo», rispose la donna, «così moriremo tutti di fame: non ti resta che piallare le assi e preparare le bare.»",
"“你真是疯了，”女人说，“那样我们全会饿死：你只好刨木板、备棺材了。”"),

("E non gli lasciò pace finché lui finì per accosentire anche se disse: «Ma i miei poveri figli mi fanno pietà».",
"她纠缠不休，直到他终于答应，尽管他说：“可我可怜的孩子们真叫我心疼。”"),

("Anche i due bambini non riuscivano a prender sonno dalla fame e avevano udito bene quello che la matrigna aveva detto al padre.",
"两个孩子也饿得睡不着，把继母对父亲说的话听得一清二楚。"),

("Gretel piangeva lacrime amare e disse ad Hänsel: «Per noi è proprio finita».",
"格蕾特哭得伤心，对韩塞尔说：“我们这下完了。”"),

("«Taci Gretel», disse Hänsel, «non ti angosciare, ci penserò io.»",
"“别作声，格蕾特，”韩塞尔说，“别发愁，我有办法。”"),

# SEC3 — Hänsel raccoglie i sassolini
("E quando i due vecchi si furono addormentati, si alzò, infilò la giacca, aprì la porta sul retro e sgattaiolò fuori.",
"两个大人睡着以后，他爬起来，套上外套，推开后门，悄悄溜了出去。"),

("Splendeva una luna chiara e i sassolini bianchi davanti a casa rilucevano come talleri nuovi; Hänsel si chinò e se ne riempì le tasche più che potè.",
"月色清亮，屋前的小白石子像新铸的钱币一样闪闪发光；韩塞尔弯下腰，把口袋装得满满的。"),

("Poi tornò indietro e disse a Gretel: «Consolati, cara sorellina, e dormi tranquilla. Dio non ci abbandonerà» e anche lui si mise a letto.",
"然后他回来对格蕾特说：“放心吧，好妹妹，安稳睡下。上帝不会抛下我们的。”他也上了床。"),

# SEC4 — la prima gita nel bosco
("Allo spuntar dell'alba, ancora prima che sorgesse il sole, la donna andò a svegliare i due bambini: «Alzatevi, pigroni, andiamo nel bosco a far legna».",
"天刚蒙蒙亮，太阳还没出来，女人就来叫两个孩子起床：“起来，懒虫们，跟我们进林子砍柴去。”"),

("Poi diede ad ognuno un pezzettino di pane e disse: «Eccovi qualcosa per il pranzo, ma non mangiatelo prima, che dell'altro non ne riceverete».",
"她给每人一小块面包，说：“这是你们的午饭，可别提前吃，回头再没有了。”"),

("Gretel nascose il pane sotto il grembiule perché Hänsel aveva le tasche piene di sassolini.",
"格蕾特把面包藏进围裙，因为韩塞尔的口袋装满了石子。"),

("Poi, tutti insieme, s'incamminarono per la strada del bosco.",
"于是大家一道走上了林间小路。"),

("Quando ebbero fatto un pezzetto di strada, Hänsel si girò a guardare la casa e così fece più volte.",
"走了一段路，韩塞尔回头望望屋子，还一次次地回头。"),

("Il padre disse: «Cosa guardi Hänsel e perché rimani sempre indietro, sta attento a dove metti i piedi».",
"父亲说：“韩塞尔，你老看什么，干嘛总落在后头，当心脚下。”"),

("«Ah padre», disse Hänsel, «guardo il mio gattino bianco che se ne sta sul tetto e che vuole dirmi addio».",
"“啊，父亲，”韩塞尔说，“我在看屋顶上那只小白猫，它正跟我道别呢。”"),

("La donna disse: «Sciocco, quello non è il tuo gatto, ma il sole del mattino che brilla sul comignolo».",
"女人说：“傻瓜，那不是你的猫，是清晨照在烟囱上的太阳。”"),

("In realtà Hänsel non si era curato del gattino, ma aveva buttato sulla strada ogni volta uno dei sassolini bianchi che aveva in tasca.",
"其实韩塞尔根本没管什么猫，只是把口袋里的小白石子一颗颗丢在路上。"),

# SEC5 — abbandonati vicino al fuoco
("Arrivati proprio in mezzo al bosco, il padre disse: «Raccogliete legna, bambini, voglio accendere un fuoco, perché non geliate».",
"到了树林正当中，父亲说：“孩子们，捡柴吧，我要生堆火，免得你们冻着。”"),

("Hänsel e Gretel raccolsero rami secchi, una bella montagnola.",
"韩塞尔和格蕾特捡来干枝，堆起一座小山。"),

("Furono accesi e quando la fiamma bruciava proprio bene, la donna disse: «Mettetevi accanto al fuoco, cari bambini, e riposate, noi andiamo nel bosco a tagliar legna. Quando avremo finito, torneremo a prendervi».",
"火生起来了，当火焰正旺时，女人说：“孩子们，挨着火坐着歇会儿，我们进林子砍柴。砍完了就来接你们。”"),

("Hänsel e Gretel rimasero accanto al fuoco, e quando venne mezzogiorno, ognuno mangiò il suo pezzetto di pane.",
"韩塞尔和格蕾特守在火边，到了中午，各自吃了那小块面包。"),

("E poiché udivano i colpi dell'ascia, credevano che il babbo fosse vicino.",
"他们听见斧头声，以为父亲就在近旁。"),

("Ma non era l'ascia, era un ramo che il padre aveva legato ad un albero secco e che il vento faceva battere.",
"可那不是斧头，是父亲拴在枯树上、被风吹得拍打作响的树枝。"),

("Eran lì da un pezzo, e alla fine i loro occhi si chiusero dalla stanchezza ed essi si addormentarono profondamente.",
"他们待了很久，终于累得闭上眼，沉沉地睡熟了。"),

# SEC6 — ritorno a casa coi sassolini
("Quando si svegliarono era già notte.",
"等他们醒来，已是夜里。"),

("Gretel si mise a piangere e disse: «Come usciremo dal bosco?».",
"格蕾特哭起来，说：“咱们怎么出得了林子？”"),

("Ma Hänsel la consolò e disse: «Aspetta ancora un po' fino a quando non sorga la luna, allora troveremo la strada».",
"韩塞尔安慰她说：“再等会儿，等月亮升起来，咱们就能找到路了。”"),

("E quando la luna piena fu alta nel cielo, Hänsel prese la sorellina per mano e seguì i sassolini che brillavano come talleri nuovi e segnavano la via.",
"当一轮明月高悬天上，韩塞尔拉着妹妹的手，顺着像新钱币般发亮、指明道路的小石子走去。"),

("Camminarono tutta la notte e allo spuntar del giorno raggiunsero la casa del loro padre.",
"他们走了一整夜，天亮时到了父亲的家。"),

("Bussarono alla porta e quando la donna aprì e vide che erano Hänsel e Gretel disse: «Cattivi bambini, perché avete dormito così a lungo nel bosco? Pensavamo non voleste più tornare».",
"他们敲门，女人开门一见是韩塞尔和格蕾特，就说：“坏孩子，你们在林子里睡那么久干吗？我们还以为你们不回来了呢。”"),

("Ma il padre si rallegrò perché gli era pesato il cuore a lasciarli lì così da soli.",
"可父亲却很高兴，因为把孩子们独自丢下，他心里一直不好受。"),

# SEC7 — il secondo piano / briciole
("Non passò molto tempo e la miseria premeva ad ogni angolo e i bambini udivano la matrigna che a letto durante la notte diceva al padre: «È di nuovo finito tutto, non c'è rimasto che una mezza pagnotta, poi sarà la fine. I bambini debbono andarsene, li porteremo nel bosco ancora più fondo così che non ritrovino la strada — altrimenti per noi non c'è scampo».",
"没过多久，困苦逼得家家户户难熬，孩子们又听见继母夜里在床上对父亲说：“东西又全吃光了，只剩半块面包，这下完了。孩子们得弄走，我们把他们带进更深的林子，叫他们找不到路：要不咱们没救了。”"),

("L'uomo si sentì un gran peso sul cuore e pensò: «L'ultimo pezzo di pane lo dovresti dividere coi tuoi figli».",
"男人心里沉甸甸的，想：“这最后一点面包，也该分给孩子们。”"),

("Ma la donna non voleva sentir ragione, lo rimbrottava e lo accusava: «Chi dice A deve dire anche B» e poiché la prima volta aveva ceduto, doveva cedere anche la seconda.",
"可女人不听劝，反倒数落埋怨他：“说一就得有二。”既然头一回让了步，这回也得让。"),

("I bambini erano svegli e avevano udito tutto.",
"孩子们醒着，把一切听得明明白白。"),

("Quando i vecchi si furono addormentati Hänsel si alzò di nuovo e voleva uscire a raccogliere i sassolini, come la volta precedente, ma la donna aveva chiuso a chiave la porta e Hänsel non potè uscire.",
"两个大人睡着后，韩塞尔又爬起来，想像上次那样出去捡石子，可女人把门锁上了，韩塞尔出不去。"),

("Ma consolò ugualmente la sorella e le disse: «Non piangere, Gretel, dormi in pace, il buon Dio ci aiuterà».",
"他还是安慰妹妹说：“别哭，格蕾特，安心睡，好心的上帝会帮咱们的。”"),

("All'alba venne la donna a far alzare i bambini.",
"天亮后女人来叫孩子们起床。"),

("Diede loro un pezzo di pane, che era ancora più piccolo di quello della volta precedente.",
"她给他们一块面包，比上回那块还小。"),

("Sulla strada per il bosco Hänsel lo spezzettò in tasca e spesso si fermava e buttava una briciola per terra.",
"去林子的路上，韩塞尔把面包掰碎揣在兜里，时不时停下，丢一颗面包屑在地上。"),

("«Hänsel perché ti fermi e cosa guardi?», disse il padre. «Va' avanti.»",
"“韩塞尔，你干嘛停下，看什么？”父亲说，“往前走。”"),

("«Guardo il mio piccioncino che sta sul tetto e che mi dice addio», rispose Hänsel.",
"“我看屋顶上那只小鸽子，它正跟我道别呢。”韩塞尔答道。"),

("«Ma non è il tuo piccione, ma il primo sole che brilla sul comignolo», disse la donna.",
"“那不是你的鸽子，是照在烟囱上的头一缕阳光。”女人说。"),

("Ma Hänsel continuava a gettare briciole lungo la strada.",
"可韩塞尔还是一路把面包屑撒在地上。"),

# SEC8 — abbandonati di nuovo
("La donna condusse i bambini ancora più addentro nel bosco, dove mai in vita loro erano arrivati.",
"女人把孩子们带进更深的林子，那是他们从未到过的地方。"),

("Accesero di nuovo un fuoco e la madre disse: «Restate qui, bambini, se siete stanchi dormite un po': noi andiamo nel bosco a tagliar legna e stasera, quando avremo finito, torneremo a prendervi».",
"又生起一堆火，母亲说：“孩子们，待在这儿，累了就睡会儿：我们进林子砍柴，傍晚干完了就来接你们。”"),

("Quando fu mezzogiorno, Gretel divise il suo pane con Hänsel che aveva sparso il suo per la strada.",
"到了中午，格蕾特把面包分给韩塞尔，他自己的早已撒在路上。"),

("Poi s'addormentarono, e scese la sera, ma nessuno arrivò a prendere i poveri bambini.",
"接着他们睡着了，夜幕降临，却没人来接这两个可怜的孩子。"),

("Si svegliarono che era notte fonda e Hänsel consolava la sorella e diceva: «Aspetta, Gretel, fino a quando sorgerà la luna, allora vedremo le briciole che ho sparso, quelle ci mostreranno la strada per casa».",
"他们醒来已是深夜，韩塞尔安慰妹妹说：“等等，格蕾特，等月亮升起，咱们就能看见我撒的面包屑，它们会给咱们指回家路。”"),

("Quando sorse la luna, si alzarono, ma non trovarono nemmeno una briciola: i mille e mille uccellini che volano nel bosco e nei campi le avevano beccate tutte.",
"月亮升起，他们起身，却连一颗面包屑也没找到：林里田间成千上万的小鸟把屑子全啄光了。"),

("Hänsel disse a Gretel: «Troveremo comunque la strada».",
"韩塞尔对格蕾特说：“咱们总能找到路的。”"),

("Ma non la trovarono; camminarono tutta la notte e ancora un giorno, da mattina a sera, ma non uscirono dal bosco e avevano tanta fame perché non avevano altro da mangiare che un paio di bacche trovate per terra.",
"可他们没找着；走了一整夜又一天，从早到晚，还是没出林子，饿得慌，因为除了地上捡的几颗浆果，什么也没得吃。"),

("Erano talmente stanchi, che le gambe non li reggevano più, si sdraiarono sotto un albero e s'addormentarono.",
"他们累得腿都撑不住了，便躺在树下睡了过去。"),

# SEC9 — bosco profondo / uccellino
("Era già la terza mattina da quando avevano lasciato la casa del padre.",
"离开父亲家已经第三天早晨了。"),

("Ricominciarono a camminare, ma sempre più s'addentrarono nel fitto del bosco e stavano quasi per soccombere.",
"他们又往前走，却越走越深，眼看就要撑不住了。"),

("Quando fu mezzogiorno videro un uccellino bianco come la neve che se ne stava seduto su un ramo e cantava tanto bene che si fermarono ad ascoltarlo.",
"中午时分，他们看见一只雪白的鸟儿落在枝头，唱得那样好听，便停下听它唱。"),

("Poi l'uccellino sbattè le ali e volò davanti a loro ed essi lo seguirono finché arrivarono davanti a una casetta e l'uccellino si posò sul tetto.",
"鸟儿扑棱翅膀，飞到他们前头，他们跟着它，一直走到一座小屋前，鸟儿落在屋顶上。"),

# SEC10 — la casetta di pane
("Quando giunsero più vicini videro che la casetta era tutta fatta di pane ed era coperta di focaccia, ma le finestrelle erano di zucchero chiaro e trasparente.",
"走近一看，小屋全是用面包做的，盖着糕饼，窗户却是清亮透明的糖。"),

("«Avviciniamoci», disse Hänsel, «e facciamoci un buon pranzetto. Io voglio un pezzettino di tetto, Gretel e tu mangiati un po' della finestrella che è buona e dolce».",
"“咱们过去，”韩塞尔说，“美美吃一顿。我要啃一块屋顶，格蕾特你吃那扇甜甜的窗户吧。”"),

("Hänsel si alzò sulla punta dei piedi e si prese un pezzettino di tetto, per assaggiare di cosa sapeva e Gretel si accostò ai vetri e cominciò a rosicchiare.",
"韩塞尔踮起脚，掰了一小块屋顶尝味道，格蕾特凑到窗前，开始啃起来。"),

("Allora una vocina gridò dall'interno: «Gnam, gnam, mastichina, chi rode la mia casettina?».",
"这时里头有个细嗓门喊道：“咂吧，咂吧，小馋嘴，谁在啃我的小屋？”"),

("E i bambini risposero: «È il vento, il venticello, il bimbo del cielo».",
"孩子们答道：“是风儿，小风儿，天上的娃娃。”"),

("E continuarono a mangiare senza lasciarsi confondere.",
"他们接着吃，没被搅乱。"),

("Hänsel, al quale il tetto era piaciuto davvero, ne staccò un grosso pezzo e Gretel aveva tolto tutto un vetro rotondo, se ne stava seduta e se lo succhiava beatamente.",
"韩塞尔真爱吃屋顶，掰了一大块；格蕾特则取下整块圆窗，坐着美滋滋地吮起来。"),

# SEC11 — la strega li cattura
("Ma d'un tratto la porta s'aprì e ne uscì lentamente una donna vecchissima, che si sorreggeva con una gruccia.",
"忽然门开了，走出一个拄拐的极老的老太婆，慢吞吞的。"),

("Hänsel e Gretel si spaventarono molto e lasciarono cadere quello che avevano in mano.",
"韩塞尔和格蕾特吓坏了，把手里的东西掉在地上。"),

("La vecchia scosse il capo e disse: «Ahi, cari bambini, chi vi ha condotti qui? Entrate e rimanete con me, qui starete bene».",
"老太婆摇摇头说：“哎哟，可爱的孩子，谁把你们带到这儿来的？进来吧，留在我这儿，你们会很好的。”"),

("Li prese per mano e li portò dentro alla casetta.",
"她牵着他们的手，把他们带进小屋。"),

("Qui era preparato un buon cibo, latte e frittelle con lo zucchero, mele e noci.",
"屋里备好了好吃的：牛奶、撒糖的煎饼、苹果和核桃。"),

("Poi furono preparati due lettini con le copertine bianche e Hänsel e Gretel si coricarono e credettero d'essere in paradiso.",
"又备了两张小床，铺着白被单，韩塞尔和格蕾特躺下，觉得自己像进了天堂。"),

("La vecchia s'era comportata in maniera tanto gentile, ma in verità era una strega cattiva che irretiva e insidiava i bambini e che aveva costruito la casetta di pane proprio solo per attrarli.",
"老太婆待他们那样和善，其实是个坏女巫，专拐骗、坑害小孩子，那面包小屋正是为引他们来才搭的。"),

("Quando un bambino cadeva nelle sue mani, lo uccideva, lo cucinava e lo mangiava e per lei quello era un giorno di festa.",
"哪个孩子落进她手，就被她杀死、煮了吃掉，对她来说那是过节。"),

("Quando Hänsel e Gretel si erano avvicinati, aveva riso malignamente e si era detta beffarda: «Non mi sfuggono».",
"韩塞尔和格蕾特刚走近，她就恶毒地笑了，冷嘲道：“这下你们跑不掉啦。”"),

("La mattina presto, prima che i bambini si svegliassero, era già in piedi e quando vide come tutti e due dormivano beatamente con le guancette belle rosse e tonde, così mormorò fra sé e sé: «Sono proprio un buon boccone».",
"清早，孩子们还没醒，她已起身；见两个孩子睡得红扑扑、圆嘟嘟的胖脸蛋，便自言自语：“真是一口好肉。”"),

# SEC12 — Gretel in cucina / Hänsel ingrassa
("Allora afferrò Hänsel con le sue mani secche e lo portò in una piccola stalla.",
"她用干枯的手一把抓住韩塞尔，把他拎进一间小棚。"),

("Poteva urlare quanto voleva, ma non serviva a niente, lei lo rinchiuse dietro un cancello.",
"任他怎么喊都没用，她把他关在栅栏后头。"),

("Poi andò da Gretel, la svegliò con uno scossone e disse: «Alzati, pigraccia, va' a prender acqua e cucina qualcosa di buono per tuo fratello, è nella stalla e deve ingrassare. Quando è bello grosso me lo mangerò».",
"她走到格蕾特跟前，摇醒她说：“起来，懒丫头，去打水，给你哥做点好吃的，他在棚里，得养胖。等他肥了，我就把他吃了。”"),

("Gretel cominciò a piangere amaramente, ma fu tutto inutile, dovette fare quello che la cattiva strega pretendeva.",
"格蕾特伤心地哭，可全没用，只得照坏女巫的吩咐做。"),

("Allora per il povero Hänsel venivano preparati i cibi migliori e Gretel non riceveva che i gusci di granchio.",
"于是可怜的韩塞尔尽吃最好的饭菜，格蕾特只拿到蟹壳。"),

("Ogni mattina la vecchia si trascinava fino alla gabbia e gridava: «Hänsel metti fuori il tuo ditino, così che io possa sentire se sei grasso».",
"每天早晨老太婆拖到笼前喊：“韩塞尔，伸出你的小手指，让我摸摸你胖了没。”"),

("Ma Hänsel le porgeva un ossicino e la vecchia, che aveva gli occhi torbidi e non poteva vederlo e che credeva davvero che quelle fossero le dita di Hänsel, molto si meravigliava che non ingrassasse.",
"可韩塞尔伸给她一根小骨头，老太婆眼浑看不清，真当那是韩塞尔的手指，奇怪他怎么总不长肉。"),

("Passate quattro settimane e visto che Hänsel era ancora magro, perse la pazienza e non volle più attendere.",
"过了四个星期，见韩塞尔还是那么瘦，她没了耐性，不肯再等。"),

("«Svelta Gretel», gridò la vecchia, «porta dell'acqua, grasso o magro che sia, domani ammazzerò Hänsel e lo cucinerò».",
"“快，格蕾特，”老太婆喊，“打水去，肥的瘦的都得宰，明天我就把韩塞尔宰了煮了。”"),

("Ah, come piangeva la povera sorellina, quando dovette portar l'acqua e come le scorrevano le lacrime sulle guance.",
"可怜的妹妹去打水时哭得多么伤心，眼泪顺着脸颊直淌。"),

("«Buon Dio, aiutaci», diceva, «se almeno le bestie feroci ci avessero divorato nel bosco, almeno saremmo morti insieme».",
"“好上帝，救救我们，”她说，“哪怕林里野兽把我们吞了，起码也能死在一块儿。”"),

("«Risparmiati i tuoi piagnistei — disse la vecchia — non ti serve a niente».",
"“省省你的哭嚎吧，”老太婆说，“没用的。”"),

# SEC13 — nel forno
("La mattina presto Gretel dovette uscire, appendere il paiolo pieno d'acqua e accendere il fuoco.",
"清早格蕾特得出来，挂上装满水的锅，生起火。"),

("«Prima faremo il pane», disse la vecchia, «ho già scaldato il forno e fatto l'impasto».",
"“先烤面包，”老太婆说，“炉子我早烧热了，面也和好了。”"),

("E spinse la povera Gretel fino presso il forno dove già divampavano le fiamme.",
"她把可怜的格蕾特推到炉边，里头火苗正窜。"),

("«Infilati dentro e dimmi se è bello caldo, così che io possa infornare.»",
"“钻进去，告诉我够不够热，好让我把面包送进去。”"),

("E quando Gretel fosse stata dentro voleva chiudere il portello per arrostirla e mangiarsi anche lei.",
"等格蕾特进去，她就想关上炉门把她烤熟，连她也吃了。"),

("Ma Gretel si accorse di quello che la vecchia aveva in mente e disse: «Non so come fare per entrarvi».",
"可格蕾特看穿了老太婆的心思，说：“我不知怎么进去。”"),

("«Stupida oca», disse la vecchia, «la bocca del forno è abbastanza grande, vedi bene che ci passo anch'io».",
"“蠢鹅，”老太婆说，“炉口够大了，你看，我都能钻进去。”"),

("Così arrancò e s'arrampicò e infilò la testa nel forno.",
"于是她挪步爬高，把头探进炉子。"),

("Allora Gretel le diede una bella spinta che la mandò a finire ben dentro, chiuse lo sportello di ferro e tirò il catenaccio.",
"格蕾特使劲一推，把她推进去老远，关上铁门，闩上插销。"),

("Hii, la vecchia cominciò a urlare in maniera terribile, ma Gretel fuggì e la maledetta strega dovette miseramente bruciare.",
"嘿咿，老太婆发出可怕的尖叫，可格蕾特逃开了，这该死的女巫活活烧成了灰。"),

# SEC14 — fuga e tesoro
("Gretel corse come una furia da Hänsel, aprì la gabbia e chiamò: «Hänsel siamo salvi, la vecchia strega è morta».",
"格蕾特飞也似的跑到韩塞尔那儿，打开笼子喊：“韩塞尔，咱们得救了，老女巫死了。”"),

("Allora Hänsel saltò fuori come un uccello dalla gabbietta quando gli viene aperta la porta.",
"韩塞尔像小鸟出了笼，一下子蹦了出来。"),

("Con che gioia si saltarono al collo e si abbracciarono e baciarono.",
"他们高兴得搂住彼此的脖子，又抱又亲。"),

("E poiché non avevano più nulla da temere, entrarono nella casa della strega e dappertutto trovarono forzieri con perle e pietre preziose.",
"既然再没什么可怕的，他们走进女巫的屋子，到处都找着装满珍珠宝石的箱子。"),

("«Sono meglio dei nostri sassolini», disse Hänsel e si riempì le tasche con tutte quelle che ci entravano e Gretel disse: «Anch'io ne porterò a casa un po'», e si riempì il grembiulino.",
"“这比咱们的石子强多了，”韩塞尔说，把兜里能塞的全塞满；格蕾特也说：“我也要带点儿回家。”把围裙装得满满的。"),

("«Ma adesso scappiamo», disse Hänsel, «dobbiamo andar via dal bosco della strega».",
"“可现在快跑，”韩塞尔说，“咱们得离开女巫的林子。”"),

# SEC15 — il fiume e l'anatra
("Quando ebbero camminato un paio d'ore, giunsero a un grande corso di acqua.",
"走了一两个钟头，他们来到一条大水沟前。"),

("«Non possiamo passare», disse Hänsel, «non vedo né passerella né ponte».",
"“过不去，”韩塞尔说，“我既没见小桥也没见踏板。”"),

("«E non c'è nemmeno una barchetta», disse Gretel, «ma c'è una bianca anatra che nuota, se la prego ci aiuterà a passare».",
"“连只小船也没有，”格蕾特说，“可有只白鸭子在游，求它准能帮咱们过去。”"),

("Poi gridò: «Anatrina, anatrina, qui ci sono Hänsel e Gretel, non c'è ponte, né passerella, vieni anatrina bella».",
"她便喊：“小鸭儿，小鸭儿，这儿有韩塞尔和格蕾特，没有桥也没有板，快来呀，漂亮的小鸭儿。”"),

("E l'anatra si avvicinò e Hänsel le salì sul dorso e disse alla sorellina di sedergli accanto.",
"鸭子游过来，韩塞尔骑上它的背，叫妹妹也坐他身边。"),

("«No», disse Gretel, «sarebbe troppo pesante per lei, ci trasporterà una dopo l'altra».",
"“不，”格蕾特说，“那它太吃重了，还是一个一个驮吧。”"),

("Così fece la buona bestiolina e quando essi furono felicemente arrivati dall'altra parte camminarono ancora per un po'; il bosco pareva a loro sempre più conosciuto e infine da lontano scorsero la casa del padre.",
"好心的鸭子就这么办，等他们平安到了对岸，又往前走了一程；林子在他们眼里越来越眼熟，终于远远望见了父亲的屋子。"),

# SEC16 — ritorno a casa / finale
("Allora si misero a correre, si precipitarono nella stube e si buttarono fra le braccia del padre.",
"他们撒腿就跑，冲进堂屋，扑进父亲怀里。"),

("L'uomo da quando li aveva abbandonati nel bosco non aveva avuto più un'ora di pace, e la donna poi era morta.",
"自从把孩子们丢在林子里，这男人就没一刻安生，而那女人已经死了。"),

("Gretel rovesciò il suo grembiulino e perle e pietre preziose si sparsero per la stube e Hänsel aggiungeva a piene mani il contenuto delle sue tasche.",
"格蕾特抖开围裙，珍珠宝石撒了一地；韩塞尔也把兜里的东西一股脑儿倒出来。"),

("Così finirono tutti i guai e i tre vissero felici e contenti.",
"就这样，苦难全消，三个人快快活活过日子。"),

("La mia storia è finita.",
"我的故事讲完了。"),

("Laggiù corre un topolino, chi lo prende si potrà fare un bel berrettone di pelo.",
"那边跑过一只小老鼠，谁逮着它，就能做顶好皮帽。"),
]

# SEC grouping by narrative section (16 sections, 120 paras total)
SEC = ([1]*2 + [2]*8 + [3]*3 + [4]*9 + [5]*7 + [6]*7 + [7]*13 + [8]*8 +
       [9]*5 + [10]*7 + [11]*10 + [12]*12 + [13]*10 + [14]*6 + [15]*7 + [16]*6)
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

    # 1) data/st/15.js  (NO guard, NO src — match 11-14.js)
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
