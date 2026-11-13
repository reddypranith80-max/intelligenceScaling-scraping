"""Stats, context filter, work inference. Writes stage3.pkl and prints a review table."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pickle, collections
from dictbuild import build, U
from works import WORKS

T = pickle.load(open("texts.pkl", "rb"))
TW = pickle.load(open("textworks.pkl", "rb"))
hits, disc = pickle.load(open("stage2.pkl", "rb"))
ents = build()
ALIASW = {"Fate": "Fate (Fate/Zero, Fate/stay night)", "HPMOR": "Harry Potter and the Methods of Rationality", "Kyokou Suiri": "Kyokou Suiri (In/Spectre)",
          "Irregular at Magic High School": "The Irregular at Magic High School"}
canon = lambda w: ALIASW.get(w, w)
postidx = {t[1]: i for i, t in enumerate(T) if t[0] == "p"}

# anchors: lead characters imply their work
anchor = {n: e["work"] for n, e in ents.items() if e["work"] != U and not e["ctx"] and len(hits.get(n, [])) >= 100}
tctx = collections.defaultdict(set)
for i, ws in enumerate(TW):
    if ws:
        tctx[i] |= {canon(w) for w in ws}
for n, w in anchor.items():
    for i in hits[n]:
        tctx[i].add(w)


def ctx_of(i):
    s = set(tctx.get(i, ()))
    p = postidx.get(T[i][2])
    if p is not None and p != i:
        s |= tctx.get(p, set())
    return s


def stats(idxs):
    au = collections.Counter(T[i][3] for i in idxs)
    th = collections.Counter(T[i][2] for i in idxs)
    n = len(idxs)
    au.pop("[deleted]", None)
    return {"n": n, "authors": len(au), "threads": len(th),
            "top_author_share": (max(au.values()) / n) if au and n else 0,
            "top_thread_share": (max(th.values()) / n) if th and n else 0,
            "first": min(T[i][4] for i in idxs) if idxs else 0, "last": max(T[i][4] for i in idxs) if idxs else 0}


def infer(idxs, own=None):
    c = collections.Counter()
    for i in idxs:
        for w in tctx.get(i, ()):   # same-text evidence only
            if w != own and WORKS.get(w, ("",))[0] != "X":
                c[w] += 1
    return c


res = {}
for n, e in ents.items():
    idxs = hits.get(n, [])
    if e["ctx"]:
        idxs = [i for i in idxs if e["work"] in ctx_of(i)]
    st = stats(idxs)
    st["cow"] = infer(idxs).most_common(4)
    st["idx"] = idxs
    res[n] = st
dres = {}
for n, idxs in disc.items():
    if len(idxs) < 4:
        continue
    st = stats(idxs)
    st["cow"] = infer(idxs).most_common(4)
    st["idx"] = idxs
    dres[n] = st
pickle.dump((res, dres), open("stage3.pkl", "wb"))

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "U"
    def line(n, st, extra=""):
        return f"{n}|{st['n']}|a{st['authors']}|t{st['threads']}|{st['top_author_share']:.0%}|" + ",".join(f"{w[:22]}:{c}" for w, c in st["cow"]) + extra
    if mode == "U":
        for n, e in ents.items():
            if e["work"] == U and res[n]["n"]:
                print(line(n, res[n]))
    elif mode == "D":
        for n, st in sorted(dres.items(), key=lambda x: -x[1]["n"]):
            print(line(n, st))
    elif mode == "K":   # known-work entries whose co-mentions disagree, or thin/outlier
        for n, e in ents.items():
            st = res[n]
            if e["work"] == U or st["n"] == 0:
                continue
            cow = dict(st["cow"])
            top = st["cow"][0][0] if st["cow"] else None
            if e["type"] in ("Web novel",) and (top and top != e["work"] and cow.get(e["work"], 0) * 2 < st["cow"][0][1]) or (st["n"] >= 3 and st["top_author_share"] >= 0.7):
                print(line(n, st, f"|=> {e['work']}"))
