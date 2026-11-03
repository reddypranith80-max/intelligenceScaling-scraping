"""Archive every post and comment of a subreddit via the Arctic Shift API.

No account, API key or third-party packages needed.
Usage: python scrape_subreddit.py IntelligenceScaling
"""
import json
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://arctic-shift.photon-reddit.com/api"


def fetch(kind, subreddit, after):
    params = {"subreddit": subreddit, "limit": 100, "sort": "asc"}
    if after is not None:
        params["after"] = after
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{BASE}/{kind}/search?{qs}",
                                 headers={"User-Agent": "subreddit-archiver/1.0"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)["data"]
        except Exception as e:
            print(f"  retry {attempt + 1}: {e}", file=sys.stderr)
            time.sleep(2 ** attempt)
    raise RuntimeError("API kept failing")


def dump(kind, subreddit, path):
    after, total, seen = None, 0, set()
    with open(path, "w", encoding="utf-8") as f:
        while True:
            rows = [r for r in fetch(kind, subreddit, after) if r["id"] not in seen]
            if not rows:
                break
            for row in rows:
                seen.add(row["id"])
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            total += len(rows)
            after = rows[-1]["created_utc"] - 1  # overlap 1s; dedupe by id
            print(f"{kind}: {total}", end="\r")
            time.sleep(0.3)
    print(f"{kind}: {total} saved to {path}")


if __name__ == "__main__":
    sub = sys.argv[1] if len(sys.argv) > 1 else "IntelligenceScaling"
    dump("posts", sub, f"{sub}_posts.jsonl")
    dump("comments", sub, f"{sub}_comments.jsonl")
