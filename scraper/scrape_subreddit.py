"""Archive every post and comment of a subreddit via the Arctic Shift API.

No account, API key or third-party packages needed.

Usage:
  python scrape_subreddit.py IntelligenceScaling                 full download into the current folder
  python scrape_subreddit.py IntelligenceScaling --update data   only fetch what is newer than data/*.jsonl
                                                                 (run tools/rebuild_data.py first)
"""
import argparse
import json
import os
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


def dump(kind, subreddit, path, update=False):
    after, total, seen = None, 0, set()
    if update and os.path.exists(path):
        # resume: remember every id already saved and restart one hour before the newest row
        newest = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                seen.add(row["id"])
                newest = max(newest, int(row["created_utc"]))
        after = newest - 3600
        print(f"{kind}: {len(seen)} already saved, fetching what is newer")
    with open(path, "a" if update else "w", encoding="utf-8", newline="\n") as f:
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
    print(f"{kind}: {total} {'new rows added to' if update else 'saved to'} {path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("subreddit", nargs="?", default="IntelligenceScaling")
    ap.add_argument("--update", metavar="DIR", help="append only new posts/comments to DIR/<subreddit>_*.jsonl")
    a = ap.parse_args()
    folder = a.update or "."
    dump("posts", a.subreddit, os.path.join(folder, f"{a.subreddit}_posts.jsonl"), bool(a.update))
    dump("comments", a.subreddit, os.path.join(folder, f"{a.subreddit}_comments.jsonl"), bool(a.update))
