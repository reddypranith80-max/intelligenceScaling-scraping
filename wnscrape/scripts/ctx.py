import pickle, re, sys, datetime
T = pickle.load(open("texts.pkl","rb"))
pat = re.compile(sys.argv[1]); n = int(sys.argv[2]); w = int(sys.argv[3]); skip = int(sys.argv[4]) if len(sys.argv)>4 else 1
hits = [(t,m) for t in T for m in [pat.search(t[5])] if m]
print(len(hits), "hits; authors", len({t[3] for t,m in hits}), "threads", len({t[2] for t,m in hits}))
for t,m in hits[::max(1,skip)][:n]:
    s = t[5][max(0,m.start()-w):m.end()+w].replace("\n"," ")
    print(f"[{t[0]} {datetime.datetime.fromtimestamp(t[4], datetime.UTC):%y-%m-%d} {t[3][:10]}] {s}")
