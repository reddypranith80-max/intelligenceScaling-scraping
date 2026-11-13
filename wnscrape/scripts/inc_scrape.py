"""Fetch posts/comments newer than the existing archive and append (deduped by id)."""
import json, sys, time, urllib.parse, urllib.request, datetime
BASE = "https://arctic-shift.photon-reddit.com/api"
SUB = "IntelligenceScaling"
def fetch(kind, after):
    qs = urllib.parse.urlencode({"subreddit": SUB, "limit": 100, "sort": "asc", "after": after})
    req = urllib.request.Request(f"{BASE}/{kind}/search?{qs}", headers={"User-Agent": "subreddit-archiver/1.0"})
    for a in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)["data"]
        except Exception as e:
            print("retry", a, e, file=sys.stderr); time.sleep(2 ** a)
    raise RuntimeError("API kept failing")
data = sys.argv[1]
for kind in ("posts", "comments"):
    path = f"{data}/{SUB}_{kind}.jsonl"
    seen, mx = set(), 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line); seen.add(r["id"]); mx = max(mx, int(r["created_utc"]))
    after, new = mx - 86400, 0   # re-check last day for late-archived items
    with open(path, "a", encoding="utf-8") as f:
        while True:
            rows = fetch(kind, after)
            fresh = [r for r in rows if r["id"] not in seen]
            for r in fresh:
                seen.add(r["id"]); f.write(json.dumps(r, ensure_ascii=False) + "\n")
            new += len(fresh)
            if not rows or (not fresh and len(rows) < 100): break
            nxt = int(rows[-1]["created_utc"]) - 1
            if nxt <= after: nxt = after + 1
            after = nxt
            mx = max(mx, int(rows[-1]["created_utc"]))
            time.sleep(0.3)
    print(kind, "new:", new, "total:", len(seen), "latest:", datetime.datetime.fromtimestamp(mx, datetime.UTC))
