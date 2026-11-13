"""Builds the character dictionary: previous lists + corrections from the recheck."""
import csv, os
REPO = os.environ.get("REPO", "../repo")
U = "Undiscovered"
DROP_GROUPS = {"term", "game", "real person", "place", "slur", "painting", "Dragon Ball term", "Kaiji sound effect", "Death Note", "Monster",
 "manga", "Ghost of Tsushima", "Kingdom (manga)", "The God of High School (webtoon)", "Assassination Classroom", "poet / common name",
 "historical general", "historical general / Kingdom", "historical", "Qin Shi Huang (historical)", "Three Kingdoms (state)", "Korean name",
 "Regressor Instruction Manual", "Overgeared", "Defiance of the Fall", "Purple Days", "Super Supportive", "Paranoid Mage", "Japanese name",
 "Legend of the White Snake", "Journey to the West (classic)"}
DROP_NAMES = {"Heavenly Court", "Spring Autumn Cicada (Gu)", "Shadow Sect", "Split Souls", "Sinful Hospital", "Chusheng Demon Sect", "Cauldron",
 "Zhen Ren", "Qing Mao", "Wisdom Gu", "Fate Gu", "Kinugasa Shougo", "Arisu (ambiguous: Sakayanagi / Ryohei)", "Yang Gu", "Bai Gu", "Gu Yue"}
# variant spelling / alias entry -> canonical character (merged as alias); None = drop
MERGE = {"Fan Yuan": "Fang Yuan", "Fang Yuang": "Fang Yuan", "Fang Juan": "Fang Yuan", "Fang Yuan (Gu Yue Fang Yuan)": "Fang Yuan",
 "Henry Fang (English name of Fang Yuan)": "Fang Yuan", "Hei Luo Lan": "Hei Lou Lan", "Chen Ren": "Chen Ran", "Chan Ran": "Chen Ran", "Fake Chen Ran": "Chen Ran",
 "Qui Yinong": "Qiu Yinong", "Qiu Yining": "Qiu Yinong", "Lin Xiuan": "Lin Xuan", "Lin Shizi": "Lin Sizhi", "Lin Shizhi": "Lin Sizhi", "Niu Yudao": "Niu Youdao",
 "Pu Yunchuan": "Pun Yunchuan", "Pun Yuchuan": "Pun Yunchuan", "Thales": "Thales Jadestar", "Mu Zhixuan": "Mu Zixuan", "Ariel": "Ariel (Shadow Slave)",
 "Di Wu": "Diwu Zhiyi", "Di Wu Zhi": "Diwu Zhiyi", "Diwu Zeyi": "Diwu Zhiyi", "Wu Zeyi": "Diwu Zhiyi", "Xuan Lou": "Xuan Luo", "Bai Xuichi": "Bai Xiuchi",
 "Feng Bijue": "Feng Bujue", "Gu Qing Shan": "Gu Qingshan", "Xin Ci": "Shang Xin Ci", "Shang Xi Ci": "Shang Xin Ci", "Gu Chinsha": "Gu Chensha", "Dou Jie": "Duo Jie",
 "Chan Mou": "Chen Mou", "Yang Siliang": "Ying Siliang", "Yang Wen Li": "Yang Wenli", "Chou Ji": "Chou Jiu", "Liu Bie": "Liu Bei", "Gua Jia": "Guo Jia", "Cheng Gong": "Chen Gong",
 "The Fool (Klein)": "Klein Moretti", "Sherlock Moriarty (Klein alias)": "Klein Moretti", "Gehrman Sparrow": "Klein Moretti", "Zhou Mingrui (Klein)": "Klein Moretti",
 "Dwayne Dantes (Klein alias)": "Klein Moretti", "Mr. World (Klein alias)": "Klein Moretti", "Li Gang (Vile Dominion)": "Li Gang", "Mao Mao": "Maomao",
 "Heaven Demon Venerable": None, "Lotus Immortal Venerable": None, "Earth Immortal Venerable": None, "Sun Immortal Venerable": None}
# work corrections (character -> work); from tags found in the archive and the novels themselves
REWORK = {"Lu Yang": "Being a Talent in Chusheng Demon Sect", "Diwu Zhiyi": "18 Levels of Hell",
 "Gu Qingshan": "World's Apocalypse Online", "Feng Bujue": "Thriller Paradise", "Li Yao": "Forty Millenniums of Cultivation", "Gu Chensha": "Dragon Talisman",
 "Han Jue": "Top Tier Providence", "Ning Zhuo": "Immortal Craftsman", "Tie Ruo Nan": "Reverend Insanity", "Jia Fu": "Reverend Insanity", "Ren Zu": "Reverend Insanity",
 "Wu Shuai": "Reverend Insanity", "Mo Yao": "Reverend Insanity", "Lin Fan": U, "Ning Qiushui": U, "Lin Qi": "Blackstone Code"}
RENAME_WORK = {"Struggling to Survive in the Demonic Sect": "Being a Talent in Chusheng Demon Sect", "(unidentified web novel)": U, "(unknown, likely Chinese web novel)": U, "?": U,
 "Japanese": U, "Three Kingdoms": "Romance of the Three Kingdoms", "Three Kingdoms (Liu Bei typo)": "Romance of the Three Kingdoms", "Three Kingdoms (Guo Jia typo)": "Romance of the Three Kingdoms",
 "Three Kingdoms (Chen Gong typo)": "Romance of the Three Kingdoms", "Legend of the Galactic Heroes (novel)": "Legend of the Galactic Heroes", "The Apothecary Diaries (light novel)": "The Apothecary Diaries",
 "Chinese villain web novel (Jun Xiaoyao)": "I Am the Fated Villain", "Chinese villain web novels": "Villain: Gu Changge", "Chinese web novel protagonist name": U, "Peerless Martial God / web novels": "Martial God Asura",
 "Nightwatchman (Great Zhou)": "Nightwatcher", "My Teen Romantic Comedy (Oregairu)": "Oregairu", "Fate series": "Fate (Fate/Zero, Fate/stay night)",
 "Sherlock Holmes (Conan Doyle novels)": "Sherlock Holmes", "Shrouded in Darkness": "Shrouding the Heavens"}
TYPE = {"Romance of the Three Kingdoms": "Classic novel", "Legend of the Galactic Heroes": "Light novel", "The Apothecary Diaries": "Light novel"}
# ambiguous names: only counted when their novel (title or a lead character) appears in the same post/comment or its thread's post
CTX = {"Adam", "Amon", "Hermes", "Medici", "Coil (Thomas Calvert)", "Alexandria (Worm)", "Scion", "Sunny (Sunless)", "Cassie", "Ariel (Shadow Slave)", "Anvil (Shadow Slave)", "Albion", "Uriel",
 "Red Lotus Demon Venerable", "Giant Sun Immortal Venerable", "Great Dream Immortal Venerable", "Amadeus (Black Knight)", "Ouroboros", "George III", "Contessa", "Lynch", "Mr. A",
 "Limitless Demon Venerable", "Paradise Earth Immortal Venerable", "First Saint", "World Honoured One", "Sora (NGNL)", "Shiro (NGNL)", "Riku Dola", "Alya (Roshidere)",
 "Siesta (The Detective Is Already Dead)", "Tet", "Holo", "Accelerator", "Kyon", "William (Tower of Karma)", "Albedo", "Emilia", "Echidna", "Jibril", "Kirito", "Ender Wiggin",
 "Leto II Atreides", "Evernight Goddess", "Cattleya", "Roselle Gustav", "Wang Lin", "Lin Feng", "Yi Tian", "Tai Bai", "Ii-chan (Boku)", "Deishu Kaiki", "Ougi Oshino", "Daiya Oomine",
 "Yukinoshita Yukino", "Yukinoshita Haruno", "Kazuma Satou", "Fiel Nirvalen", "Shiina Hiyori", "Kanzaki Ryuji", "Morishita Ai", "Katsuragi Kohei", "Sakagami Kazuma", "Kijima", "Naoe",
 "Hasebe Haruka", "Onodera Kayano", "Kitou Hayato", "Yamamura Miki", "Shibata So", "Totsuka Yahiko", "Miyake Akito", "Shinohara Satsuki", "Gilgamesh", "Shirou Emiya", "Demiurge",
 "Hirata Yosuke", "Sudo Ken", "Nanase Tsubasa", "Ibuki Mio", "Tsubaki Sakurako", "Yukimura Teruhiko", "Hashimoto Masayoshi", "Matsushita Chiaki", "Mashima Tomonari", "Kamuro Masumi",
 "Horikita Manabu", "Yagami Takuya", "Amasawa Ichika", "Nagumo Miyabi", "Kei Karuizawa", "Yuki Suou", "Kuze Masachika", "Tanya Degurechaff", "Anos Voldigoad", "Wu Yong (RI)", "Thales Jadestar"}
NEW = [  # character | work | type | aliases   (added in this recheck)
 ("Lynch", "Blackstone Code", "Web novel", "!Lynch"), ("Dantalian", "Dungeon Defense", "Web novel", "dantalian"),
 ("Lee Kiyoung", "Regressor Instruction Manual", "Web novel", "lee kiyoung,kiyoung,lee ki-young"),
 ("First Saint", "Being a Talent in Chusheng Demon Sect", "Web novel", "first saint"),
 ("World Honoured One", "Being a Talent in Chusheng Demon Sect", "Web novel", "world honoured one,world honored one"),
 ("William (Tower of Karma)", "Tower of Karma", "Web novel", "william liwius,!William"),
 ("Ai Magase", "Babylon", "Novel", "ai magase,magase"), ("Zen Seizaki", "Babylon", "Novel", "seizaki"),
 ("Ii-chan (Boku)", "Zaregoto", "Light novel", "ii-chan,iichan,!Ii"), ("Jun Aikawa", "Zaregoto", "Light novel", "jun aikawa,aikawa jun"),
 ("Victorique de Blois", "Gosick", "Light novel", "victorique,victorica"), ("Aoi Hinami", "Bottom-tier Character Tomozaki", "Light novel", "aoi hinami,hinami aoi"),
 ("Beyond Birthday", "Death Note: Another Note", "Light novel", "beyond birthday,rue ryuzaki"), ("Naomi Misora", "Death Note: Another Note", "Light novel", "naomi misora,misora"),
 ("Koyomi Araragi", "Monogatari", "Light novel", "araragi"), ("Meme Oshino", "Monogatari", "Light novel", "meme oshino,oshino meme"),
 ("Deishu Kaiki", "Monogatari", "Light novel", "kaiki deishu,deishu kaiki,!Kaiki"),
 ("Tsubasa Hanekawa", "Monogatari", "Light novel", "hanekawa"), ("Ougi Oshino", "Monogatari", "Light novel", "ougi oshino,oshino ougi,!Ougi"),
 ("Accelerator", "A Certain Magical Index", "Light novel", "!Accelerator"), ("Aleister Crowley", "A Certain Magical Index", "Light novel", "aleister"),
 ("Touma Kamijou", "A Certain Magical Index", "Light novel", "kamijou,kamijo touma,touma kamijo"),
 ("Cid Kagenou", "The Eminence in Shadow", "Light novel", "cid kagenou,kagenou"),
 ("Kazuki Hoshino", "The Empty Box and Zeroth Maria", "Light novel", "kazuki hoshino,hoshino kazuki"),
 ("Aya Otonashi", "The Empty Box and Zeroth Maria", "Light novel", "aya otonashi,otonashi maria,maria otonashi"),
 ("Daiya Oomine", "The Empty Box and Zeroth Maria", "Light novel", "daiya oomine,oomine daiya,!Daiya"),
 ("Paul von Oberstein", "Legend of the Galactic Heroes", "Light novel", "oberstein"),
 ("Tatsuya Shiba", "The Irregular at Magic High School", "Light novel", "tatsuya shiba,shiba tatsuya"), ("Holo", "Spice and Wolf", "Light novel", "!Holo"),
 ("Kotoko Iwanaga", "Kyokou Suiri (In/Spectre)", "Novel", "kotoko iwanaga,iwanaga"),
 ("Rudeus Greyrat", "Mushoku Tensei", "Light novel", "rudeus"), ("Haruhi Suzumiya", "Haruhi Suzumiya", "Light novel", "haruhi suzumiya,suzumiya"),
 ("Kyon", "Haruhi Suzumiya", "Light novel", "!Kyon"),
 ("Chitanda Eru", "Hyouka", "Light novel", "chitanda"), ("Fukube Satoshi", "Hyouka", "Light novel", "fukube"), ("Irisu Fuyumi", "Hyouka", "Light novel", "irisu"),
 ("Yukinoshita Yukino", "Oregairu", "Light novel", "yukino yukinoshita,yukinoshita yukino,!Yukino"),
 ("Yukinoshita Haruno", "Oregairu", "Light novel", "haruno yukinoshita,yukinoshita haruno,!Haruno"),
 ("Roswaal L. Mathers", "Re:Zero", "Light novel", "roswaal"), ("Kimihiko Kimizuka", "The Detective Is Already Dead", "Light novel", "kimizuka"),
 ("Shizuo Heiwajima", "Durarara!!", "Light novel", "shizuo"),
 ("Jinshi", "The Apothecary Diaries", "Light novel", "jinshi"), ("Albedo", "Overlord", "Light novel", "!Albedo"),
 ("Kazuma Satou", "Konosuba", "Light novel", "kazuma satou,satou kazuma,!Kazuma"),
 ("Bell Cranel", "Danmachi", "Light novel", "bell cranel"), ("Tet", "No Game No Life", "Light novel", "!Tet"),
 ("Chlammy Zell", "No Game No Life", "Light novel", "chlammy,kurami"), ("Fiel Nirvalen", "No Game No Life", "Light novel", "fiel nirvalen,!Fiel"),
 ("Izuna Hatsuse", "No Game No Life", "Light novel", "izuna"),
 ("Kiryuin Fuuka", "Classroom of the Elite", "Light novel", "kiryuin,kiryuuin"), ("Shiina Hiyori", "Classroom of the Elite", "Light novel", "hiyori shiina,shiina hiyori,!Hiyori"),
 ("Kanzaki Ryuji", "Classroom of the Elite", "Light novel", "!Kanzaki"),
 ("Ishizaki Daichi", "Classroom of the Elite", "Light novel", "ishizaki"), ("Ishigami Kyo", "Classroom of the Elite", "Light novel", "ishigami kyo,kyo ishigami"),
 ("Morishita Ai", "Classroom of the Elite", "Light novel", "!Morishita"),
 ("Kiriyama Ikuto", "Classroom of the Elite", "Light novel", "kiriyama"), ("Utomiya Riku", "Classroom of the Elite", "Light novel", "utomiya"),
 ("Hoshinomiya Chie", "Classroom of the Elite", "Light novel", "hoshinomiya"), ("Sakagami Kazuma", "Classroom of the Elite", "Light novel", "!Sakagami"),
 ("Suzukake", "Classroom of the Elite", "Light novel", "suzukake"),
 ("Kijima", "Classroom of the Elite", "Light novel", "!Kijima"), ("Naoe", "Classroom of the Elite", "Light novel", "!Naoe"),
 ("Hasebe Haruka", "Classroom of the Elite", "Light novel", "!Hasebe"), ("Onodera Kayano", "Classroom of the Elite", "Light novel", "!Onodera"),
 ("Kitou Hayato", "Classroom of the Elite", "Light novel", "!Kitou"), ("Yamamura Miki", "Classroom of the Elite", "Light novel", "!Yamamura"),
 ("Shibata So", "Classroom of the Elite", "Light novel", "!Shibata"),
 ("Ike Kanji", "Classroom of the Elite", "Light novel", "ike kanji,kanji ike"), ("Totsuka Yahiko", "Classroom of the Elite", "Light novel", "!Totsuka"),
 ("Albert Yamada", "Classroom of the Elite", "Light novel", "albert yamada,yamada albert"),
 ("Asahina Nazuna", "Classroom of the Elite", "Light novel", "asahina nazuna,nazuna asahina"), ("Tachibana Akane", "Classroom of the Elite", "Light novel", "tachibana akane,akane tachibana"),
 ("Miyake Akito", "Classroom of the Elite", "Light novel", "!Miyake"), ("Sato Maya", "Classroom of the Elite", "Light novel", "sato maya,maya sato"),
 ("Shinohara Satsuki", "Classroom of the Elite", "Light novel", "!Shinohara"),
]


def build():
    ents = {}

    def add(name, work, typ, aliases, src):
        e = ents.setdefault(name, {"work": work, "type": typ, "aliases": set(), "src": src})
        e["aliases"] |= {a.strip() for a in aliases if a.strip()}

    pend = []
    for r in csv.DictReader(open(f"{REPO}/results/web_novel_characters.csv", encoding="utf-8-sig")):
        n, w = r["character"], r["work"]
        al = r["aliases"].split(", ")
        if n in MERGE:
            if MERGE[n] is None:
                continue
            pend.append((MERGE[n], al))
            continue
        if w in DROP_GROUPS or n in DROP_NAMES:
            continue
        w = RENAME_WORK.get(w, w)
        add(n, w, TYPE.get(w, "Web novel"), al, "previous list")
    for r in csv.DictReader(open(f"{REPO}/results/characters_all.csv", encoding="utf-8-sig")):
        if r["medium"] not in ("Light novel", "Novel", "Classic novel"):
            continue
        n, w = r["character"], RENAME_WORK.get(r["work"], r["work"])
        if n in DROP_NAMES or w == "(community-made novel)":
            continue
        al = []
        for a in r["aliases_matched"].split("; "):
            a = a.strip()
            if not a or len(a.split()) > 3:
                continue
            al.append(a if (" " in a or len(a) >= 8) else "!" + a.capitalize())
        if n not in ents:
            add(n, w, r["medium"], al, "repo (all characters)")
    for n, al in pend:
        if n in ents:
            ents[n]["aliases"] |= set(al)
        else:
            add(n, U, "Web novel", al, "previous list")
    for n, w, t, al in NEW:
        if n not in ents:
            add(n, w, t, al.split(","), "added in recheck")
    for n, w in REWORK.items():
        if n in ents:
            ents[n]["work"] = w
    for n in ents:
        ents[n]["ctx"] = n in CTX
    return ents


if __name__ == "__main__":
    import collections
    e = build()
    print(len(e), collections.Counter(v["type"] for v in e.values()))
