import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pickle, re, collections
T = pickle.load(open("texts.pkl","rb"))
S = pickle.load(open("summary.pkl","rb"))
res, dres = pickle.load(open("stage3.pkl","rb"))
names = [n for n,(w,t,c) in S["final"].items() if t in ("Web novel",) ]
names += ["Chen Xiao","Long Chian","Bai Ding Zhe","Gu Shiyan","Xin Shuguang","Chen Yifan","Jing He","Chen Rui","Shi Jiang","Pai Xi","Pai Xu","Satoshi","Blight","Kaito"]
bad = re.compile(r"^(ch|chapter|vol|volume|eos|current|composite|\?|v\d|c\d|\d|all|i |not|high|mid|low|no |ln|wn|novel|debat|larp|will|the mc|mc|prime|base|end|start|arc|year|pre|post|imo|still|who|which|aka|or |and |if |he |she |his|with|from|after|before|same|full|only|maybe|probably|as |at |in |on |by |so |but|though|because|except|also|even|like|my |is |was|has|had|can|not|yes|idk|forgot|i forgot|spoiler|ep\b|scaling)", re.I)
out = {}
for n in dict.fromkeys(names):
    core = re.sub(r" \(.*\)$", "", n)
    pat = re.compile(re.escape(core).replace(r"\ ", r"\s?") + r"\s?[\(\[]\s?([^\)\]\n]{3,70}?)\s?[\)\]]", re.I)
    c = collections.Counter()
    for t in T:
        for m in pat.finditer(t[5]):
            g = m.group(1).strip(" *>!<")
            if g and not bad.match(g): c[g.lower()] += 1
    if c: out[n] = c.most_common(3)
for n,v in out.items():
    print(f"{n} [{S['final'].get(n,('-',))[0][:28]}] :: " + " | ".join(f"{g}:{k}" for g,k in v))
