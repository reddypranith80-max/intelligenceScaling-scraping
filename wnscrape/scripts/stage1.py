import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pickle, re, collections
from works import WORKS, compile_works
T = pickle.load(open("texts.pkl","rb"))
CW = compile_works()
tw = []
for t in T:
    tx = t[5]
    tw.append(frozenset(w for w,ps in CW.items() if any(p.search(tx) for p in ps)))
pickle.dump(tw, open("textworks.pkl","wb"))
# token n-gram index: every Capitalised 1-3gram and all lowercase 1-4 grams would be huge; instead index tokens per text lazily in stage2
tok = re.compile(r"[A-Za-z\u00c0-\u024f0-9]+(?:[-'’][A-Za-z\u00c0-\u024f]+)*")
toks = []
for t in T:
    l = tok.findall(t[5])
    toks.append([re.sub(r"['’]s$", "", x) for x in l])
pickle.dump(toks, open("toks.pkl","wb"), protocol=5)
print("ok", sum(map(len,toks)))
