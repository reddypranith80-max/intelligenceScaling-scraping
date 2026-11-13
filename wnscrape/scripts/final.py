"""Apply the recheck rules and write all output files."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pickle, csv, collections, datetime
import dictbuild as D
from dictbuild import build, U
from works import WORKS

OUT = sys.argv[1]
REPO = os.environ["REPO"]
T = pickle.load(open("texts.pkl", "rb"))
res, dres = pickle.load(open("stage3.pkl", "rb"))
ents = build()
NP = sum(1 for t in T if t[0] == "p"); NC = int(os.environ.get("NCOMMENTS", len(T) - NP))
d = lambda ts: datetime.datetime.fromtimestamp(ts, datetime.UTC).strftime("%d %b %Y")
FIRST, LAST = d(min(t[4] for t in T)), d(max(t[4] for t in T))

# ---- discovered names kept after manual triage of the candidate list
DISC_RULE = ["Han Fei", "Tie Xue Leng", "Fang Di Chang", "Zhao Lian Yun", "Wang Xiao", "Xu Tuo", "Ma Xiu", "Li Annan", "Chu Yun", "Chen Nuo", "Gu Wen", "Lin Qin",
             "Ma Wenjie", "Ye Qiuwei", "Su Luxia", "Ning Ye", "Zi Yue", "Qi Si", "Dong Pai Xi", "Wu Ying", "Ye Min", "Luo Po", "Wang Da", "Cheng Xia Yi", "Dong Li Yai",
             "Feng Xiao", "Hua Changchen", "Shin Woo Jin"]
DISC_FIXED = {"Yan Zhaoge": ("History's Strongest Senior Brother", "Web novel"), "Seo Hweol": ("A Regressor's Tale of Cultivation", "Web novel"),
              "Jang Ilso": ("Return of the Mount Hua Sect", "Web novel"), "Li Dian": ("Romance of the Three Kingdoms", "Classic novel"),
              "Yan Liang": ("Romance of the Three Kingdoms", "Classic novel"), "Xu Chu": ("Romance of the Three Kingdoms", "Classic novel"),
              "Liu Ye": ("Romance of the Three Kingdoms", "Classic novel"), "Hua Tuo": ("Romance of the Three Kingdoms", "Classic novel")}
DISC_MERGE = {"Fang Yaun": "Fang Yuan", "Bai Ning": "Bai Ning Bing", "Lin Sinzhi": "Lin Sizhi", "Li Sinzhi": "Lin Sizhi", "Pun Yuanchan": "Pun Yunchuan",
              "Pun Yunshuan": "Pun Yunchuan", "Diwu Zheyi": "Diwu Zhiyi", "Sung Jin Woo": "Sung Jinwoo", "Hong Yun": "Ma Hong Yun"}
WTYPE = {w: {"WN": "Web novel", "LN": "Light novel", "CN": "Classic novel"}.get(t[0]) for w, t in WORKS.items()}
WTYPE.update({"Fate (Fate/Zero, Fate/stay night)": "Light novel", "Harry Potter and the Methods of Rationality": "Web novel"})


def rule(st):
    """co-mention rule: returns work or None"""
    cow = [(w, c) for w, c in st["cow"] if WTYPE.get(w) in ("Web novel", "Light novel")]
    if not cow:
        return None
    w, c = cow[0]
    second = cow[1][1] if len(cow) > 1 else 0
    if c >= 3 and c >= 0.5 * st["n"] and c >= 2 * second and st["authors"] >= 2 and st["top_author_share"] < 0.7:
        return w
    return None


final = {}      # name -> dict(work,type,st,src,how)
changes = {"dropped": [], "merged": [], "rework": [], "added": [], "identified": [], "outlier": [], "zero": []}
for n, e in ents.items():
    st = res[n]
    if st["n"] == 0:
        changes["zero"].append((n, e["work"]))
        continue
    work, typ, how = e["work"], e["type"], "labelled"
    if work == U:
        w = rule(st)
        if w:
            work, typ, how = w, WTYPE[w], "inferred from co-mentions"
            changes["identified"].append((n, w, st))
        elif st["n"] >= 3 and st["authors"] <= 1:
            changes["outlier"].append((n, "only one user ever wrote this name", st))
            continue
    final[n] = {"work": work, "type": typ, "st": st, "src": e["src"], "how": how}
for n, tgt in DISC_MERGE.items():
    if n in ents and n in final:
        del final[n]
    changes["merged"].append((n, tgt))
for n in DISC_RULE:
    st = dres.get(n)
    if not st:
        continue
    w = rule(st)
    if not w and st["authors"] <= 1:
        changes["outlier"].append((n, "only one user ever wrote this name", st))
        continue
    final[n] = {"work": w or U, "type": WTYPE[w] if w else "Web novel", "st": st, "src": "discovered in recheck", "how": "inferred from co-mentions" if w else ""}
for n, (w, t) in DISC_FIXED.items():
    if n in dres:
        final[n] = {"work": w, "type": t, "st": dres[n], "src": "discovered in recheck", "how": "labelled"}

# ---- overrides from explicit "Character (Novel)" tags found in the archive
FORCE = {"Colonel Timo": "Solo Max-Level Newbie", "Mo Tan": "Quadruple Split", "Shen Jihan": "An Ordinary Path Through the Incredulous (subreddit original story)",
         "Xue Yin": "The Endless Food Chain (subreddit original story)", "Xuan Luo": "Endless Wonders Beyond Human Imagination", "Chen Xiao": "Waking Up Finding Myself Burdened with 40 Murders",
         "Qin Cheng": "God's Imitator", "Wang Yongxin": "God's Imitator", "Cao Haichuan": "God's Imitator", "Su Chen": "Divine Throne of Primordial Blood",
         "Lin Feng": "Peerless Martial God", "Shen Lang": "Ultimate Son-in-Law", "Luo Lan": "Otherworldly Thief Emperor", "Yu Xing": "Absurd Deduction Game",
         "Bai Zhi": "Underworld Player", "Xue Huai": "Your Excellency, the Prime Minister", "Tang Jie": "Aspiring to the Immortal Path",
         "Gu Changge": "I Am the Fated Villain", "Jun Xiaoyao": "Villain of Destiny (Jun Xiaoyao)", "Dao Tianqi": "Being a Talent in Chusheng Demon Sect"}
FORCE_U = ["Bai Ding Zhe", "Long Chian", "Chen Yifan", "Xin Shuguang", "Gu Shiyan", "Shiro Nai", "Shiba Taizen", "Shinza Bansho", "Riko Rinda", "Kie Hojo", "Shinji Shikai", "Lin Fan"]
LATE_MERGE = {"Lin Qi": "Lynch", "Lin Qie": "Lynch", "Lou Lan": "Hei Lou Lan", "Li Annan": "Baili Qiangsheng"}
LATE_DROP = {"Ba Ku": "misspelling of Baku (Usogui, manga)"}
for n, w in FORCE.items():
    if n in final:
        final[n]["work"], final[n]["type"], final[n]["how"] = w, "Web novel", "tagged in the archive"
for n in FORCE_U:
    if n in final:
        final[n]["work"], final[n]["how"] = U, ""
for n, tgt in LATE_MERGE.items():
    if final.pop(n, None):
        changes["merged"].append((n, tgt))
for n, why in LATE_DROP.items():
    if final.pop(n, None):
        changes["dropped"].append((n, "(unknown, likely Chinese web novel)", why))
changes["identified"] = [(n, final[n]["work"]) for n in final if n in ents and ents[n]["work"] == U and final[n]["work"] != U]
UNK = {"(unidentified web novel)", "(unknown, likely Chinese web novel)", "?", "Japanese", "Chinese web novel protagonist name"}

# ---- changes against the previous web novel list
prev = {r["character"]: r for r in csv.DictReader(open(f"{REPO}/results/web_novel_characters.csv", encoding="utf-8-sig"))}
for n, r in prev.items():
    pw = r["work"]
    if n in LATE_MERGE or n in LATE_DROP:
        continue
    if n in D.MERGE:
        if D.MERGE[n] is None:
            changes["dropped"].append((n, pw, "fragment of a longer title, not a separate character"))
        else:
            changes["merged"].append((n, D.MERGE[n]))
    elif pw in D.DROP_GROUPS or n in D.DROP_NAMES:
        changes["dropped"].append((n, pw, "not a novel character (term, place, real person, title, item or other medium)"))
    elif n in final and final[n]["work"] != pw and not (pw in UNK and final[n]["work"] == U):
        changes["rework"].append((n, "Undiscovered" if pw in UNK else pw, final[n]["work"]))
for n, f in final.items():
    if n not in prev and f["src"] != "repo (all characters)":
        changes["added"].append((n, f["work"]))

# ---- outlier audit on what is kept
audit = []
for n, f in final.items():
    st = f["st"]
    fl = []
    if st["n"] < 3:
        fl.append("fewer than 3 mentions")
    if st["n"] >= 3 and st["authors"] <= 1:
        fl.append("single user")
    elif st["n"] >= 5 and st["top_author_share"] >= 0.7:
        fl.append("one user wrote 70%+ of mentions")
    if st["n"] >= 5 and st["top_thread_share"] >= 0.8:
        fl.append("80%+ of mentions in one thread")
    if fl:
        audit.append((n, f["work"], st, "; ".join(fl)))

# ---- write
os.makedirs(OUT, exist_ok=True)
SECT = [("Web novel", "Web novels"), ("Light novel", "Light novels"), ("Novel", "Other novels (print)"), ("Classic novel", "Classic novels")]
known = {n: f for n, f in final.items() if f["work"] != U}
und = {n: f for n, f in final.items() if f["work"] == U}
byw = collections.defaultdict(list)
for n, f in known.items():
    byw[(f["type"], f["work"])].append(n)
sk = lambda s: s.lower().lstrip("( ")
cnt = collections.Counter(f["type"] for f in known.values())
nworks = collections.Counter(t for t, w in byw)

with open(f"{OUT}/characters.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh); w.writerow(["character", "novel", "type"])
    for n, f in sorted(final.items(), key=lambda x: (x[1]["work"] == U, x[1]["type"] != "Web novel", sk(x[1]["work"]), sk(x[0]))):
        w.writerow([n, f["work"], "" if f["work"] == U else f["type"]])
with open(f"{OUT}/outlier_check.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh); w.writerow(["character", "novel", "mentions", "users", "threads", "top_user_share", "top_thread_share", "flag"])
    fl = {a[0]: a[3] for a in audit}
    for n, f in sorted(final.items(), key=lambda x: -x[1]["st"]["n"]):
        st = f["st"]
        w.writerow([n, f["work"], st["n"], st["authors"], st["threads"], f"{st['top_author_share']:.2f}", f"{st['top_thread_share']:.2f}", fl.get(n, "")])

head = f"Source: r/IntelligenceScaling archive, {NP:,} posts and {NC:,} comments, {FIRST} to {LAST}."
with open(f"{OUT}/CHARACTERS.md", "w", encoding="utf-8") as fh:
    fh.write(f"# Web novel and light novel characters in r/IntelligenceScaling\n\n{head}\n\n")
    fh.write(f"{len(final)} characters: {cnt['Web novel']} web novel, {cnt['Light novel']} light novel, {cnt['Novel'] + cnt['Classic novel']} other novel, {len(und)} undiscovered. Listed alphabetically by novel, not by mentions.\n")
    for typ, title in SECT:
        fh.write(f"\n## {title}\n\n| Character | Novel |\n|---|---|\n")
        for (t, wk), names in sorted(byw.items(), key=lambda x: sk(x[0][1])):
            if t == typ:
                for n in sorted(names, key=sk):
                    fh.write(f"| {n} | {wk} |\n")
    fh.write(f"\n## Undiscovered\n\nNames used like characters whose novel could not be confirmed from the archive.\n\n| Character | Novel |\n|---|---|\n")
    for n in sorted(und, key=sk):
        fh.write(f"| {n} | Undiscovered |\n")
with open(f"{OUT}/NOVELS.md", "w", encoding="utf-8") as fh:
    fh.write(f"# Novels and their characters\n\n{head}\n")
    for typ, title in SECT:
        fh.write(f"\n## {title} ({nworks[typ]})\n\n| Novel | Characters |\n|---|---|\n")
        for (t, wk), names in sorted(byw.items(), key=lambda x: sk(x[0][1])):
            if t == typ:
                fh.write(f"| {wk} | {', '.join(sorted(names, key=sk))} |\n")
with open(f"{OUT}/UNDISCOVERED.md", "w", encoding="utf-8") as fh:
    fh.write(f"# Undiscovered\n\n{head}\n\n{len(und)} names that are used like character names but whose novel could not be confirmed. "
             "A name stays here unless a novel title or one of its lead characters appears in at least half of the posts and comments that use the name, from at least two users.\n\n"
             "| Character | Novel |\n|---|---|\n")
    for n in sorted(und, key=sk):
        fh.write(f"| {n} | Undiscovered |\n")
with open(f"{OUT}/CHANGES.md", "w", encoding="utf-8") as fh:
    fh.write(f"# Changes from the previous list\n\nPrevious list: `results/WEB_NOVEL_CHARACTERS.md` in the repo (469 rows, data to 3 Nov 2026). This recheck: data to {LAST}, {len(final)} characters.\n")
    fh.write(f"\n## Novel corrected ({len(changes['rework'])})\n\n| Character | Was | Now |\n|---|---|---|\n")
    for n, a, b in sorted(changes["rework"], key=lambda x: (x[2] == U, sk(x[2]), sk(x[0]))):
        fh.write(f"| {n} | {a} | {b} |\n")
    fh.write(f"\n## Removed: not a novel character ({len(changes['dropped'])})\n\n| Name | Was listed under | Reason |\n|---|---|---|\n")
    for n, a, b in sorted(changes["dropped"], key=lambda x: sk(x[0])):
        fh.write(f"| {n} | {a} | {b} |\n")
    fh.write(f"\n## Merged: spelling variants and aliases ({len(changes['merged'])})\n\n| Variant | Merged into |\n|---|---|\n")
    for n, a in sorted(changes["merged"], key=lambda x: (sk(x[1]), sk(x[0]))):
        fh.write(f"| {n} | {a} |\n")
    fh.write(f"\n## Removed: single-user outliers ({len(changes['outlier'])})\n\n| Name | Mentions | Users | Reason |\n|---|---|---|---|\n")
    for n, a, st in sorted(changes["outlier"], key=lambda x: sk(x[0])):
        fh.write(f"| {n} | {st['n']} | {st['authors']} | {a} |\n")
    fh.write(f"\n## Removed: never mentioned ({len(changes['zero'])})\n\nSearched by name and found 0 times (ambiguous single-word names count only next to their novel).\n\n| Name | Novel |\n|---|---|\n")
    for n, a in sorted(changes["zero"], key=lambda x: (sk(x[1]), sk(x[0]))):
        fh.write(f"| {n} | {a} |\n")
    fh.write(f"\n## Added ({len(changes['added'])})\n\nNames searched or found for the first time in this recheck. The light novel and print novel characters already hand-checked in the repo (`characters_all.csv`) are also in CHARACTERS.md but are not counted here.\n\n| Character | Novel |\n|---|---|\n")
    for n, a in sorted(changes["added"], key=lambda x: (sk(x[1]), sk(x[0]))):
        fh.write(f"| {n} | {a} |\n")
with open(f"{OUT}/OUTLIER_CHECK.md", "w", encoding="utf-8") as fh:
    fh.write(f"# Outlier check\n\n{head}\n\nEvery kept character was checked for who wrote its mentions and where. {len(audit)} of {len(final)} are flagged below; they stay on the list because the name itself is a real character, but the evidence is thin. Full numbers for every character are in `outlier_check.csv`.\n\n"
             "| Character | Novel | Mentions | Users | Threads | Flag |\n|---|---|---|---|---|---|\n")
    for n, wk, st, fl in sorted(audit, key=lambda x: (sk(x[1]), sk(x[0]))):
        fh.write(f"| {n} | {wk} | {st['n']} | {st['authors']} | {st['threads']} | {fl} |\n")
pickle.dump({"final": {n: (f["work"], f["type"], f["st"]["n"]) for n, f in final.items()}, "changes": {k: len(v) for k, v in changes.items()},
             "cnt": dict(cnt), "nworks": dict(nworks), "und": len(und), "audit": len(audit), "NP": NP, "NC": NC, "FIRST": FIRST, "LAST": LAST}, open("summary.pkl", "wb"))
print(len(final), dict(cnt), "und", len(und), "works", dict(nworks), {k: len(v) for k, v in changes.items()}, "audit", len(audit), NP, NC, FIRST, LAST)
print("identified:", len(changes["identified"]))
print("disc:", "; ".join(f"{n}->{final[n]['work']}" for n in DISC_RULE if n in final))
