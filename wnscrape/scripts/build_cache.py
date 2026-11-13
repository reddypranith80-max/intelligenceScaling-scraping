import json, pickle, sys, html
data = sys.argv[1]; out = []
with open(f"{data}/IntelligenceScaling_posts.jsonl", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        st = r.get("selftext") or ""
        if st in ("[removed]", "[deleted]"): st = ""
        out.append(("p", r["id"], r["id"], r.get("author") or "", int(r["created_utc"]), html.unescape((r.get("title") or "") + "\n" + st)))
with open(f"{data}/IntelligenceScaling_comments.jsonl", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        b = r.get("body") or ""
        if b in ("[removed]", "[deleted]"): continue
        out.append(("c", r["id"], (r.get("link_id") or "")[3:], r.get("author") or "", int(r["created_utc"]), html.unescape(b)))
pickle.dump(out, open("texts.pkl", "wb"), protocol=5)
print(len(out), sum(len(x[5]) for x in out))
