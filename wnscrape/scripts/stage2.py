"""Match every dictionary character + discover new pinyin/Korean-style names. Writes stage2.pkl."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pickle, re, collections
from dictbuild import build

T = pickle.load(open("texts.pkl", "rb"))
TOK = pickle.load(open("toks.pkl", "rb"))
TW = pickle.load(open("textworks.pkl", "rb"))
ents = build()
tok = re.compile(r"[A-Za-zÀ-ɏ0-9]+(?:[-'’][A-Za-zÀ-ɏ]+)*")


def key(a):
    return tuple(re.sub(r"['’]s$", "", x).lower() for x in tok.findall(a))


amap = {}  # token tuple -> list of (name, case_sensitive)
for n, e in ents.items():
    for a in e["aliases"]:
        cs = a.startswith("!")
        k = key(a.lstrip("!"))
        if k:
            amap.setdefault(k, []).append((n, cs))
maxn = max(len(k) for k in amap)

PIN = re.compile(r"^(zh|ch|sh|[bpmfdtnlgkhjqxrzcsyw])?(a|o|e|i|u|ai|ei|ao|ou|an|en|ang|eng|ong|ia|ie|iao|iu|ian|in|iang|ing|iong|ua|uo|uai|ui|uan|un|uang|ue|er)$")
# also joined two-syllable given names (Zhiyuan, Youdao, Renjun ...)
PIN2 = re.compile(r"^(?:(zh|ch|sh|[bpmfdtnlgkhjqxrzcsyw])?(a|o|e|i|u|ai|ei|ao|ou|an|en|ang|eng|ong|ia|ie|iao|iu|ian|in|iang|ing|iong|ua|uo|uai|ui|uan|un|uang|ue|er)){1,2}$")
SURN = set("li wang zhang liu chen yang zhao huang zhou wu xu sun hu zhu gao lin he guo ma luo liang song zheng xie han tang feng yu dong xiao cheng cao yuan deng fu shen zeng peng lu su jiang cai jia ding wei xue ye yan pan du dai xia zhong tian ren fang shi yao tan sheng zou xiong jin hao kong bai cui kang mao qiu qin gu hou shao meng long wan duan qian yin yi mo ning niu mu ji qi gui xuan geng tie pun ang shu diwu baili bo chu jun ou ru shang lou ling xin xing hei hua ge zi dao tao chou duo si ying cui lan nie ruan lei fan fei gong qu ke pu".split())
KSURN = set("kim lee park choi jung kang cho yoon jang lim han oh seo shin kwon hwang ahn song yoo hong jeon ko moon baek nam ha noh jin woo sung cha".split())
STOP = set("the a an and or but if so to of in on at for with by is it he she we you i me my his her its our they them this that these those not no yes can do did does has had have was were be been are will would could should may might must as from up out all any one two him who what why how when where than then too very just also more most some such only own same now can man men fun run sun gun win pin bin ban fan pan ran tan dan long song hang sang bang die lie pie tie she me he we her hen pen ten den men mean lean bean dean jean sean chin shin thin main gain pain rain lain wait bait gui make take like".split())

hits = collections.defaultdict(list)       # name -> text idx
disc = collections.defaultdict(list)       # discovered candidate -> text idx
for idx, toks in enumerate(TOK):
    if not toks:
        continue
    low = [t.lower() for t in toks]
    seen = set()
    L = len(toks)
    covered = [False] * L
    for i in range(L):
        for n in range(min(maxn, L - i), 0, -1):
            k = tuple(low[i:i + n])
            v = amap.get(k)
            if not v:
                continue
            for name, cs in v:
                if cs and not toks[i][:1].isupper():
                    continue
                if name not in seen:
                    seen.add(name)
                    hits[name].append(idx)
                for j in range(i, i + n):
                    covered[j] = True
    # discovery: 2-3 capitalised tokens, first is a surname, rest pinyin
    dseen = set()
    i = 0
    while i < L - 1:
        if toks[i][:1].isupper() and not toks[i].isupper() and not covered[i]:
            f = low[i]
            if (f in SURN or f in KSURN) and len(f) > 1:
                j = i + 1
                while j < L and j < i + 3 and toks[j][:1].isupper() and not toks[j].isupper() and not covered[j] and (PIN2.match(low[j]) or f in KSURN) and low[j] not in STOP and len(low[j]) > 1:
                    j += 1
                if j > i + 1:
                    c = " ".join(t.capitalize() for t in low[i:j])
                    if c not in dseen:
                        dseen.add(c)
                        disc[c].append(idx)
                    i = j
                    continue
        i += 1

pickle.dump((dict(hits), dict(disc)), open("stage2.pkl", "wb"))
print("dictionary chars with hits:", len(hits), "of", len(ents))
print("discovered candidates >=5:", sum(1 for v in disc.values() if len(v) >= 5))
