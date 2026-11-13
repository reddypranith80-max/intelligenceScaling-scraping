"""List every novel character discussed in r/IntelligenceScaling, with the novel each one is from.

Usage: python analysis/novel_characters.py [--data data] [--out results]

Reads the raw archive (run tools/rebuild_data.py first) and analysis/novel_catalog.txt, checks every catalog
entry against the archive and writes:

  results/NOVEL_CHARACTERS.md / novel_characters.csv        every character and its novel
  results/WEB_NOVEL_CHARACTERS.md / web_novel_characters.csv
  results/LIGHT_NOVEL_CHARACTERS.md / light_novel_characters.csv
  results/OTHER_NOVEL_CHARACTERS.md / other_novel_characters.csv
  results/UNDISCOVERED_CHARACTERS.md / undiscovered_characters.csv
  results/NOVELS.md                                          every novel, by type
  results/novel_characters_evidence.csv                      the counts behind the lists (the recheck)

The lists hold two fields only: character and novel. A character is listed only if the archive mentions it.
Ambiguous names (catalog prefix "~") count only when their novel is named in the same post/comment or in the
post the comment belongs to, so a stray "Adam" or "Kirito" does not create an entry.
Standard library only.
"""
import argparse
import csv
import datetime
import json
import os
import re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
TOK = re.compile(r"[A-Za-z0-9À-ÿ]+(?:['’][A-Za-z]+)*")
TYPES = [("web", "Web novels"), ("community", "Community-written web fiction"), ("light", "Light novels"),
         ("novel", "Other published novels")]


def tokens(text):
    """Words with a trailing possessive removed: "Fang Yuan's" -> Fang, Yuan."""
    out = []
    for t in TOK.findall(text):
        t = t.replace("’", "'")
        if t.endswith("'s") or t.endswith("'S"):
            t = t[:-2]
        if t:
            out.append(t)
    return out


def load_catalog(path):
    works, chars = {}, []          # works: title -> {"type", "aliases"};  chars: dicts
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            p = line.split("|")
            if p[0] == "N":
                works[p[2]] = {"type": p[1], "aliases": [a.strip() for a in p[3].split(",") if a.strip()]}
            elif p[0] in ("C", "U"):
                work, name, al = (p[1], p[2], p[3]) if p[0] == "C" else ("", p[1], p[2] if len(p) > 2 else "")
                if p[0] == "C" and work not in works:
                    raise SystemExit(f"catalog line {n}: unknown novel {work!r}")
                al = [a.strip() for a in al.split(",") if a.strip()]
                if al and al[0] == "-":
                    al = al[1:]
                else:
                    al = [name] + al
                chars.append({"name": name, "work": work, "aliases": al})
            else:
                raise SystemExit(f"catalog line {n}: bad record type {p[0]!r}")
    return works, chars


def build_index(works, chars):
    """lowercased token tuple -> list of (kind, id, exact-case tuple or None, gated)."""
    idx = defaultdict(list)

    def add(alias, kind, eid):
        gated = case = False
        while alias[:1] in "~!":
            gated |= alias[0] == "~"
            case |= alias[0] == "!"
            alias = alias[1:]
        toks = tokens(alias)
        if toks:
            idx[tuple(t.lower() for t in toks)].append((kind, eid, tuple(toks) if case else None, gated))

    wid = {w: i for i, w in enumerate(works)}
    for w, d in works.items():
        add(w, "w", wid[w])
        for a in d["aliases"]:
            add(a, "w", wid[w])
    for i, c in enumerate(chars):
        for a in c["aliases"]:
            add(a, "c", i)
    return idx, wid, max(len(k) for k in idx)


def scan(text, idx, maxn):
    """Greedy longest-match scan. Returns (works named, characters, gated characters)."""
    toks = tokens(text)
    low = [t.lower() for t in toks]
    ws, cs, gs = set(), set(), set()
    i, n = 0, len(toks)
    while i < n:
        step = 1
        for j in range(min(n, i + maxn), i, -1):
            ents = idx.get(tuple(low[i:j]))
            if not ents:
                continue
            hit = False
            for kind, eid, exact, gated in ents:
                if exact is not None and tuple(toks[i:j]) != exact:
                    continue
                hit = True
                if kind == "w":
                    ws.add(eid)
                elif gated:
                    gs.add(eid)
                else:
                    cs.add(eid)
            if hit:
                step = j - i
                break
        i += step
    return ws, cs, gs


def iter_rows(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def clean(s):
    return "" if s in (None, "[removed]", "[deleted]") else s


def day(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d") if ts else ""


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def md(s):
    return s.replace("|", "\\|")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="results")
    ap.add_argument("--sub", default="IntelligenceScaling")
    ap.add_argument("--catalog", default=os.path.join(HERE, "novel_catalog.txt"))
    args = ap.parse_args()
    works, chars = load_catalog(args.catalog)
    idx, wid, maxn = build_index(works, chars)
    cwork = [wid.get(c["work"], -1) for c in chars]

    posts = comments = 0
    first_ts = last_ts = None
    thread_ctx = {}
    n_posts = Counter(); n_comments = Counter(); n_ctx = Counter(); first = {}; last = {}

    def tally(kind, ts, ws, cs, gs, tctx):
        ctx = set(ws) | {cwork[c] for c in cs if cwork[c] >= 0}
        allctx = ctx | tctx
        found = set(cs) | {c for c in gs if cwork[c] in allctx}
        own = ctx | {cwork[c] for c in found}
        for c in found:
            (n_posts if kind == "p" else n_comments)[c] += 1
            # "in context": the novel's title or another of its characters is named alongside
            others = set(ws) | tctx | {cwork[x] for x in found if x != c}
            if cwork[c] in others:
                n_ctx[c] += 1
            if c not in first or ts < first[c]:
                first[c] = ts
            if c not in last or ts > last[c]:
                last[c] = ts
        return own

    for d in iter_rows(os.path.join(args.data, f"{args.sub}_posts.jsonl")):
        text = clean(d.get("title")) + "\n" + clean(d.get("selftext"))
        ts = int(d["created_utc"]); posts += 1
        first_ts = ts if first_ts is None else min(first_ts, ts)
        last_ts = ts if last_ts is None else max(last_ts, ts)
        ws, cs, gs = scan(text, idx, maxn)
        thread_ctx[d["id"]] = tally("p", ts, ws, cs, gs, set())
    for d in iter_rows(os.path.join(args.data, f"{args.sub}_comments.jsonl")):
        ts = int(d["created_utc"]); comments += 1
        last_ts = max(last_ts, ts)
        body = clean(d.get("body"))
        if not body:
            continue
        ws, cs, gs = scan(body, idx, maxn)
        if ws or cs or gs:
            tally("c", ts, ws, cs, gs, thread_ctx.get((d.get("link_id") or "")[3:], set()))

    span = f"{day(first_ts)} to {day(last_ts)}"
    head = (f"Source: the full r/IntelligenceScaling archive, {posts:,} posts and {comments:,} comments, {span} (UTC).\n"
            "Every name below is mentioned in the archive at least once, and its novel was checked against what the "
            "posts and comments themselves say.\n")
    os.makedirs(args.out, exist_ok=True)

    listed, dropped, ev = [], [], []
    for i, c in enumerate(chars):
        total = n_posts[i] + n_comments[i]
        typ = works[c["work"]]["type"] if c["work"] else "undiscovered"
        ev.append([c["name"], c["work"], typ, total, n_posts[i], n_comments[i],
                   f"{n_ctx[i] / total:.2f}" if total and c["work"] else "", day(first.get(i)), day(last.get(i)),
                   "; ".join(c["aliases"])])
        (listed if total else dropped).append((typ, c["work"], c["name"]))
    ev.sort(key=lambda r: (-r[3], r[0]))
    write_csv(os.path.join(args.out, "novel_characters_evidence.csv"),
              ["character", "novel", "type", "mentions", "posts", "comments", "share_with_novel_named",
               "first_mentioned", "last_mentioned", "names_matched"], ev)

    key = lambda s: s.lower().removeprefix("the ").removeprefix("a ")
    by_type = defaultdict(lambda: defaultdict(list))
    for typ, work, name in listed:
        by_type[typ][work].append(name)
    und = sorted(by_type["undiscovered"][""], key=str.lower)

    def section(typ, level="##"):
        out = []
        for work in sorted(by_type[typ], key=key):
            out.append(f"{level} {md(work)}\n")
            out += [f"- {md(n)}" for n in sorted(by_type[typ][work], key=str.lower)]
            out.append("")
        return out

    def pairs(typ):
        return [[n, w] for w in sorted(by_type[typ], key=key) for n in sorted(by_type[typ][w], key=str.lower)]

    def count(typ):
        return sum(len(v) for v in by_type[typ].values())

    files = {"web": ("WEB_NOVEL_CHARACTERS", "web_novel_characters", "Web novel characters"),
             "light": ("LIGHT_NOVEL_CHARACTERS", "light_novel_characters", "Light novel characters"),
             "novel": ("OTHER_NOVEL_CHARACTERS", "other_novel_characters", "Characters from other published novels")}
    for typ, (mdname, csvname, title) in files.items():
        lines = [f"# {title} in r/IntelligenceScaling\n", head]
        if typ == "web":
            lines.append(f"**{count('web') + count('community')} characters from {len(by_type['web']) + len(by_type['community'])} "
                         f"web novels**, grouped by novel, A to Z. Characters whose novel could not be identified are in "
                         f"[UNDISCOVERED_CHARACTERS.md](UNDISCOVERED_CHARACTERS.md).\n")
            lines += section("web")
            lines.append("---\n\n# Community-written web fiction\n\nStories written by members of the subreddit "
                         "themselves and discussed there like any other novel.\n")
            lines += section("community")
            rows = pairs("web") + pairs("community")
        else:
            lines.append(f"**{count(typ)} characters from {len(by_type[typ])} novels**, grouped by novel, A to Z.\n")
            lines += section(typ)
            rows = pairs(typ)
        with open(os.path.join(args.out, mdname + ".md"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines).rstrip() + "\n")
        write_csv(os.path.join(args.out, csvname + ".csv"), ["character", "novel"], rows)

    with open(os.path.join(args.out, "UNDISCOVERED_CHARACTERS.md"), "w", encoding="utf-8") as f:
        f.write("# Undiscovered: characters whose novel could not be identified\n\n" + head +
                f"\n**{len(und)} characters.** They are discussed as novel characters, but the archive never names "
                "the novel, or the novel is untranslated/private and deliberately not shared, so no source could be "
                "confirmed.\n\n" + "\n".join(f"- {md(n)}" for n in und) + "\n")
    write_csv(os.path.join(args.out, "undiscovered_characters.csv"), ["character", "novel"], [[n, "Undiscovered"] for n in und])

    total = sum(count(t) for t, _ in TYPES)
    lines = ["# Every novel character in r/IntelligenceScaling\n", head,
             f"**{total + len(und)} characters**: {count('web')} from web novels, {count('community')} from "
             f"community-written web fiction, {count('light')} from light novels, {count('novel')} from other "
             f"published novels, and {len(und)} undiscovered.\n",
             "| Character | Novel |", "|---|---|"]
    allrows = []
    for typ, _ in TYPES:
        allrows += pairs(typ)
    allrows.sort(key=lambda r: (key(r[1]), r[0].lower()))
    allrows += [[n, "Undiscovered"] for n in und]
    lines += [f"| {md(n)} | {md(w)} |" for n, w in allrows]
    with open(os.path.join(args.out, "NOVEL_CHARACTERS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    write_csv(os.path.join(args.out, "novel_characters.csv"), ["character", "novel"], allrows)

    lines = ["# Every novel discussed in r/IntelligenceScaling\n", head]
    for typ, title in TYPES:
        lines.append(f"## {title} ({len(by_type[typ])})\n")
        lines += [f"- {md(w)}" for w in sorted(by_type[typ], key=key)]
        lines.append("")
    with open(os.path.join(args.out, "NOVELS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    print(f"{posts:,} posts, {comments:,} comments, {span}")
    for typ, title in TYPES:
        print(f"  {title}: {count(typ)} characters, {len(by_type[typ])} novels")
    print(f"  Undiscovered: {len(und)}")
    print(f"  not mentioned in the archive (left out): {len(dropped)}")
    for typ, work, name in dropped:
        print(f"    - {name} ({work or 'undiscovered'})")


if __name__ == "__main__":
    main()
