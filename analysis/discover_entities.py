"""Discover and count every character, work and arc mentioned in r/IntelligenceScaling.

Unlike analyze_mentions.py (a hand-written dictionary), this script finds names itself:

  pass 1  scans all post titles, post bodies and comments for
          - "X vs Y" title sides and "Name (Work)" patterns   -> evidence a name is a character
          - mid-sentence Capitalized Sequences                -> candidate names (any frequency)
          - "<words> arc" / "<Words> Game"                    -> candidate arcs
  build   merges aliases, links characters to works, infers each work's medium
  pass 2  counts every name, work and arc across all text (case-insensitive) and writes the reports

Usage: python analysis/discover_entities.py --data data --out results [--sample N]
Standard library only.
"""
import argparse
import csv
import pickle
import datetime
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_mentions as base  # curated seed dictionary

YEARS = [2023, 2024, 2025, 2026]
DISCOVER_WORKS = False   # parenthetical tags are mostly scoring categories, so works are hand-reviewed instead

# ---------------------------------------------------------------- regexes
CAPTOK = r"[A-Z][A-Za-z'’]*[a-z][A-Za-z'’]*(?:-[A-Z][a-z]+)?"
CONN = r"(?:of|the|no|de|von|van|vi|la|le|da|di|du|el|bin)"
SEQ = re.compile(
    r"(?:(?<=[a-z0-9,;:)] )|(?<=[(\[/&\"“]))"
    rf"({CAPTOK}(?: (?:{CONN} )*{CAPTOK}){{0,4}})")
LOWTOK = re.compile(r"(?<![A-Za-z'’])[a-z][a-z'’]{2,}")
TOK = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’\-]*")
PAREN = re.compile(r"((?:[A-Z][\w'’\-]*[ ]){0,2}[A-Z][\w'’\-]*) ?\(([^()\n]{2,45})\)")
VS = re.compile(r"\s+(?:vs\.?|v\.?|versus|and|&)\s+|\s*,\s*", re.I)
VS_TITLE = re.compile(r"\b(?:vs\.?|versus)\b", re.I)
ARC = re.compile(r"((?:[A-Za-z0-9'’\-]+ ){1,4}?)arcs?\b", re.I)

ARC_LEAD_STOP = set("""the a an in on at of to from and or vs with for by during after before whole entire this that
these those his her their its our your my one two three first second third last final next previous current early
late main every each any all some other same new old story whole best worst full part which what whose after
just only even also still really actually basically literally never ever whole entire throughout since into
through over under across against between like than as is are was were be been being has have had do does did
not no yes can could would should will may might must who whom how why when where if then so but because
about around up out off more most less least many much few lot lots very too quite rather such own""".split())
ARC_GENERIC = set("redemption villain filler training tournament romance revenge character development".split())

MODIFIER_WORDS = set("""canon comp composite base manga anime novel novels ln wn pm mhe fn doc docs normal diff high mid low
extreme tier tiers scaling version versions feats feat anti buff nerf upscale downscale rated post image pic vs
form prime source edit meme joke opinion imo lol lmao ai chapter chapters ch vol volume ep episode season part
round day and or the a of in to is i it not you he she they we this that my his her their cat mouse fixed
non no yes who wins win lose pic verse game games show series film movie""".split())
JUNK_SIDE = set("""who wins win what diff tier scaling round match part canon vs which better smarter smartest
how why when where can does is are would will if the a an this that these those do did should about on in to of
and or for with from by at as it its be been being has have had not no yes ok please help need want think thought
know like just also only even still more most less least many much few lot very too quite rather such own same
tournament poll thread post question discussion opinion rate rating ranking list top best worst""".split())

META = set("""view poll diff comp canon game games characters character intelligence situation situations skills skill
cat mouse doc docs novel novels tier rank thread post question list top best worst fsiq psi vsi vci wmi fri cpi scd
pm fn mhe cote ctw ngnl overall strategy planning reasoning thinking deception manipulation foresight adaptability
intuition emotional social logical knowledge perception tactics analysis psychology misdirection concealment
fabrication countering deductive inductive abductive observation insight kind types type kinds sides side
live action very high mid low neg extreme no yes base prime composite normal tournament match round""".split())
SENT_START = set("""because also however honestly actually maybe probably basically literally personally imo yes no ok well so
then now here there still just only even but and or if when while although though since unless until after before
thanks thank please sorry hello hey hi guys everyone anyone someone nobody people one all both each every some
what why how who which where when this that these those""".split())

FUNC_NEXT = set("""the a an to of in on at by for with from this that these those it its and or as than into is are was
were be been has have had not no so but if when while novel novels tier tiers feat feats years year end future zero""".split())

MEDIUM_KEYS = {
    "manga": "Manga", "anime": "Anime", "novel": "Novel", "novels": "Novel", "ln": "Light novel",
    "wn": "Web novel", "webnovel": "Web novel", "manhwa": "Webtoon", "manhua": "Webtoon",
    "webtoon": "Webtoon", "comic": "Comic", "comics": "Comic", "film": "Film", "movie": "Film",
    "series": "TV", "season": "TV", "episode": "TV", "show": "TV", "vn": "Visual novel",
}

REGEX_ALIAS_FIX = {
    "vs L\\b": ["vs L"], "\\bL vs": ["L vs"], "!L's": None,
    "Dr\\.? ?Stone": ["Dr Stone"], "Dr\\.? Frost": ["Dr Frost"], "Bungou? Stray Dogs": ["Bungo Stray Dogs", "Bungou Stray Dogs"],
    "Re:? ?Zero": ["Re Zero", "ReZero"], "!Saw\\b": "!Saw", "In/Spectre": ["In Spectre"],
    "Fate/": ["Fate Grand Order", "Fate Stay Night"], "!You Netflix": None,
}


# ---------------------------------------------------------------- helpers
def utc(ts):
    return datetime.datetime.fromtimestamp(int(ts), datetime.UTC)


def clean_tok(t):
    t = t.lower()
    if t.endswith("'s") or t.endswith("’s"):
        t = t[:-2]
    return t.strip("-'’")


def toks_of(text):
    return [clean_tok(t) for t in TOK.findall(text)], TOK.findall(text)


def iter_docs(path, kind):
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            yield d


def title_case(key):
    small = {"of", "the", "no", "de", "von", "van", "vi", "la", "le", "da", "di", "du", "el", "bin"}
    return " ".join(w if (w in small and i) else w[:1].upper() + w[1:] for i, w in enumerate(key.split()))


# ---------------------------------------------------------------- pass 1
def pass1(posts_path, comments_path, sample):
    seqs = Counter()            # capitalized sequence -> docs
    midcap = Counter()          # token (lower) -> docs where it appears capitalized mid-sentence
    low = Counter()             # lowercase token -> uses
    vs_sides = Counter()
    pairs = defaultdict(Counter)    # lower subject -> Counter(lower content)
    arcs = Counter()
    template_docs = 0
    template_tok = Counter()
    n = Counter()

    def scan(text, is_title=False, is_post=False, in_template=False):
        found = set(SEQ.findall(text))
        for s in found:
            seqs[s] += 1
            for t in set(re.split(r" |-", s)):
                midcap[t.lower()] += 1
        low.update(LOWTOK.findall(text))
        if in_template:
            for s in found:
                for t in set(s.split(" ")):
                    template_tok[t.lower()] += 1
        for m in PAREN.finditer(text):
            subj, content = m.group(1), m.group(2).strip()
            pairs[subj.lower()][content.lower()] += 1
        for m in ARC.finditer(text):
            w = m.group(1).strip().lower().split()
            while w and w[0] in ARC_LEAD_STOP:
                w.pop(0)
            if w and not (set(w) <= ARC_LEAD_STOP) and w[-1] not in ARC_GENERIC and len(" ".join(w)) > 2:
                arcs[" ".join(w) + " arc"] += 1
        for s in found:
            parts = s.split(" ")
            if parts[-1] in ("Game", "Games", "Match", "Saga") and len(parts) > 1:
                arcs[s.lower()] += 1

    for i, d in enumerate(iter_docs(posts_path, "posts")):
        if sample and i >= sample:
            break
        n["posts"] += 1
        title = d["title"]
        body = d.get("selftext") or ""
        if VS_TITLE.search(title):
            t = re.sub(r"\([^()]*\)|\[[^\]]*\]", " ", title)
            t = re.split(r"[:|]", t)[-1] if len(t) > 70 else t
            for side in VS.split(re.sub(r"(?i)^(round|match)[^:]*:", "", t)):
                side = re.sub(r"[^A-Za-z'’\- ]", " ", side).strip()
                words = side.lower().split()
                if 1 <= len(words) <= 5 and len(side) > 2:
                    vs_sides[" ".join(clean_tok(w) for w in words)] += 1
        in_t = "FSIQ" in body
        if in_t:
            template_docs += 1
        scan(title + "\n" + body, is_post=True, in_template=in_t)
    for i, d in enumerate(iter_docs(comments_path, "comments")):
        if sample and i >= sample * 10:
            break
        n["comments"] += 1
        scan(d.get("body") or "")
        if n["comments"] % 100000 == 0:
            print(f"  pass1 comments {n['comments']:,}", flush=True)
            if len(seqs) > 6_000_000:
                for k in [k for k, v in seqs.items() if v == 1]:
                    del seqs[k]
    return dict(seqs=seqs, midcap=midcap, low=low, vs=vs_sides, pairs=pairs, arcs=arcs,
                template_docs=template_docs, template_tok=template_tok, n=n)


# ---------------------------------------------------------------- build entities
class Entities:
    def __init__(self):
        self.ents = []          # dict per entity
        self.alias = {}         # alias string (lower, space joined) -> (eid, cs)

    def add(self, kind, name, work="", medium="", tier="", aliases=()):
        eid = len(self.ents)
        self.ents.append(dict(id=eid, kind=kind, name=name, work=work, medium=medium, tier=tier, aliases=[]))
        for a in aliases:
            self.add_alias(eid, a)
        return eid

    def add_alias(self, eid, alias):
        cs = alias.startswith("!")
        a = alias[1:] if cs else alias
        key = " ".join(clean_tok(t) for t in TOK.findall(a))
        if not key:
            return
        if key not in self.alias:
            self.alias[key] = (eid, cs)
            self.ents[eid]["aliases"].append(key)


def build(p1, ents_out):
    seqs, midcap, low = p1["seqs"], p1["midcap"], p1["low"]
    tdocs = max(p1["template_docs"], 1)
    template = {t for t, c in p1["template_tok"].items() if c >= max(10, 0.20 * tdocs)}
    junk = template | META | JUNK_SIDE | SENT_START

    def ratio(t):
        m, l = midcap[t], low[t]
        return m / (m + l) if m + l else 1.0

    def is_common(t):
        return midcap[t] + low[t] >= 30 and ratio(t) < 0.12

    # --- seed: curated characters and works
    E = ents_out
    seed_char = {}
    for name, work, medium, aliases in base.CHARACTERS:
        als = []
        for a in aliases:
            if a in REGEX_ALIAS_FIX:
                fx = REGEX_ALIAS_FIX[a]
                als += [] if fx is None else ([fx] if isinstance(fx, str) else fx)
            elif "\\" in a or "?" in a:
                continue
            else:
                als.append(a)
        seed_char[name] = E.add("character", name, work, medium, "A (curated)", als)
    seed_work = {}
    for name, aliases in base.WORKS:
        als = []
        for a in aliases:
            if a in REGEX_ALIAS_FIX:
                fx = REGEX_ALIAS_FIX[a]
                als += [] if fx is None else ([fx] if isinstance(fx, str) else fx)
            elif "\\" in a or "?" in a:
                continue
            else:
                als.append(a)
        seed_work[name] = E.add("work", name, "", "", "curated", als + [name])
    def norm_work(w):
        return re.sub(r"\s*\(.*?\)", "", w).strip().lower()

    work_norm = {norm_work(n): eid for n, eid in seed_work.items()}

    def ensure_work(work, medium, tier):
        """Return the work entity for a character's work label, creating it when new."""
        n = norm_work(work)
        if n in work_norm:
            return work_norm[n]
        key = " ".join(clean_tok(t) for t in TOK.findall(work))
        safe = len(key.split()) > 1 or (len(key) >= 5 and not is_common(key))
        eid = E.add("work", work, "", medium, tier, [key] if safe and key not in E.alias else [])
        work_norm[n] = eid
        seed_work[work] = eid
        return eid

    for name, work, medium, _ in base.CHARACTERS:
        if work and not work.startswith("("):
            ensure_work(work, medium, "curated")

    # --- works discovered from parentheses: contents attached to >= 2 distinct subjects
    content_subjects = defaultdict(set)
    content_total = Counter()
    for subj, cs_ in p1["pairs"].items():
        for content, c in cs_.items():
            words = content.split()
            if not words or len(content) < 3 or len(words) > 6:
                continue
            if set(words) <= (MODIFIER_WORDS | META | template) or re.match(r"^(ch|chapter|vol|volume|ep|episode|s\d|season|part|round|day)\b", content):
                continue
            if any(w in ("diff", "vs", "scaling", "version", "feats", "tier", "canon", "buff", "nerf", "upscale") for w in words):
                continue
            content_subjects[content].add(subj)
            content_total[content] += c
    discovered_works = [] if not DISCOVER_WORKS else [c for c, s in content_subjects.items() if len(s) >= 2 and content_total[c] >= 3]
    work_alias_index = {}
    for name, eid in seed_work.items():
        for a in E.ents[eid]["aliases"]:
            work_alias_index[a] = eid
    for c in sorted(discovered_works, key=lambda c: -content_total[c]):
        key = " ".join(clean_tok(t) for t in TOK.findall(c))
        if not key or key in work_alias_index or key in E.alias:
            continue
        if len(key.split()) == 1 and (is_common(key) or len(key) < 4):
            continue
        eid = E.add("work", title_case(key), "", "", "discovered", [key])
        work_alias_index[key] = eid

    # --- reviewed names (hand-labelled from the candidate list) join the curated seed
    reviewed_chars, reviewed_works = [], []
    try:
        import reviewed_names as rv
        reviewed_chars, reviewed_works = rv.CHARACTERS, rv.WORKS
    except ImportError:
        pass
    try:
        for cname, extra in rv.EXTRA.items():
            if cname in seed_char:
                for a_ in extra:
                    E.add_alias(seed_char[cname], a_)
    except NameError:
        pass
    for name, work, medium, aliases in reviewed_chars:
        if name in seed_char:
            for a_ in aliases:
                E.add_alias(seed_char[name], a_)
            continue
        eid = E.add("character", name, work, medium, "A (reviewed)", list(aliases) + [name])
        seed_char[name] = eid
    for name, medium, aliases in reviewed_works:
        n_ = norm_work(name)
        if n_ in work_norm:
            for a_ in aliases:
                E.add_alias(work_norm[n_], a_)
            if medium and not E.ents[work_norm[n_]]["medium"]:
                E.ents[work_norm[n_]]["medium"] = medium
        else:
            eid_w = E.add("work", name, "", medium, "reviewed", list(aliases) + [name])
            seed_work[name] = work_norm[n_] = eid_w
            for a_ in E.ents[eid_w]["aliases"]:
                work_alias_index[a_] = eid_w
    for name, work, medium, _ in reviewed_chars:
        if work and not work.startswith("("):
            eid_w = ensure_work(work, medium, "reviewed")
            for a_ in E.ents[eid_w]["aliases"]:
                work_alias_index[a_] = eid_w

    # --- candidate names: every capitalized mid-sentence phrase (>= 2 documents), with evidence counts
    def clean_words(words):
        w = [t for t in words if t not in junk and len(t) > 1]
        if len(w) == 1 and is_common(w[0]):
            return []
        return w

    evid = Counter()
    for side, c in p1["vs"].items():
        w = clean_words(side.split())
        if w and len(w) <= 3:
            evid[" ".join(w)] += c
    for subj, cs_ in p1["pairs"].items():
        w = clean_words([clean_tok(t) for t in subj.split()])
        if w and len(w) <= 3:
            evid[" ".join(w)] += sum(cs_.values())

    def trim(seq):
        parts = seq.split(" ")
        while parts and (parts[-1].lower() in junk or (len(parts) > 1 and is_common(parts[-1].lower()))):
            parts.pop()
        while parts and parts[0].lower() in junk:
            parts.pop(0)
        return " ".join(parts)

    def key_of(s_):
        return " ".join(clean_tok(t) for t in TOK.findall(s_))

    seq_cand = Counter()
    for s_, c in seqs.items():
        if c < 2:
            continue
        t = trim(s_)
        if not t or any(w.lower() in junk for w in t.split(" ") if w.lower() not in {"of", "the"})                 or all(is_common(w.lower()) or w.lower() in {"of", "the"} for w in t.split(" ")):
            continue
        seq_cand[key_of(t)] += c
    created = {}
    for k, c in sorted(seq_cand.items(), key=lambda kv: -kv[1]):
        if not k or k in E.alias or k in work_alias_index:
            continue
        toks = k.split()
        if len(toks) == 1 and (is_common(toks[0]) or len(toks[0]) < 4):
            continue
        flip = " ".join(sorted(toks))
        if flip in created:
            E.add_alias(created[flip], k)
            continue
        created[flip] = E.add("candidate", title_case(k), "", "", "C (unreviewed)", [k])
        E.ents[created[flip]]["evidence"] = evid.get(k, 0)
        E.ents[created[flip]]["docs"] = c

    # --- link discovered characters to works via "Name (Work)" parentheticals
    for e in E.ents:
        if e["kind"] not in ("character", "candidate") or e["work"] or e.get("merged_into") is not None:
            continue
        votes = Counter()
        for a in e["aliases"]:
            for content, c in p1["pairs"].get(a, {}).items():
                ckey = key_of(content)
                if ckey in work_alias_index:
                    votes[E.ents[work_alias_index[ckey]]["name"]] += c
        if votes:
            e["work"] = votes.most_common(1)[0][0]
    return E, template, dict(is_common=is_common, ratio=ratio)


# ---------------------------------------------------------------- pass 2
def pass2(E, arcs_keep, posts_path, comments_path, sample, helpers):
    alias = E.alias
    maxn = max((len(k.split()) for k in alias), default=1)
    first = {k.split()[0] for k in alias}
    cs_tokens = {}
    for k, (eid, cs) in alias.items():
        if len(k.split()) == 1:
            t = k
            cs_tokens[t] = cs or (helpers["is_common"](t))
    for a in arcs_keep:
        first.add(a.split()[0])
    arc_alias = {a: a for a in arcs_keep}
    maxn = max(maxn, max((len(a.split()) for a in arcs_keep), default=1))

    posts = Counter(); comments = Counter(); titles = Counter(); score_sum = Counter()
    yearc = defaultdict(Counter)
    first_ts, last_ts = {}, {}
    thread_comments = Counter()
    arc_docs = Counter(); arc_score = Counter(); arc_year = defaultdict(Counter)
    arc_char = defaultdict(Counter); arc_work = defaultdict(Counter)
    work_med = defaultdict(Counter)
    monthly = defaultdict(Counter)
    act_posts = Counter(); act_comments = Counter()
    top_threads = []

    def hits_of(text):
        toks = TOK.findall(text)
        low = [clean_tok(t) for t in toks]
        eids, arcs = set(), set()
        i, N = 0, len(low)
        while i < N:
            t = low[i]
            if t not in first:
                i += 1
                continue
            matched = 0
            for n in range(min(maxn, N - i), 0, -1):
                k = " ".join(low[i:i + n])
                if k in alias:
                    eid, cs = alias[k]
                    if n == 1 and (cs or cs_tokens.get(k)):
                        if not toks[i][:1].isupper():
                            continue
                        if helpers["is_common"](k) and i + 1 < N and low[i + 1] in FUNC_NEXT:
                            continue
                    eids.add(eid)
                    matched = n
                    break
                if k in arc_alias:
                    arcs.add(k)
                    matched = n
                    break
            i += matched or 1
        return eids, arcs, set(low) if eids else None

    def record(eids, arcs, lowset, kind, ts, score):
        y = utc(ts).year
        for e in eids:
            (posts if kind == "post" else comments)[e] += 1
            score_sum[e] += score
            yearc[e][y] += 1
            monthly[e][utc(ts).strftime("%Y-%m")] += 1
            if e not in first_ts or ts < first_ts[e]:
                first_ts[e] = ts
            if e not in last_ts or ts > last_ts[e]:
                last_ts[e] = ts
        chars = [e for e in eids if E.ents[e]["kind"] == "character"]
        works = [e for e in eids if E.ents[e]["kind"] == "work"]
        for a in arcs:
            arc_docs[a] += 1
            arc_score[a] += score
            arc_year[a][y] += 1
            for c in chars:
                arc_char[a][c] += 1
            for w in works:
                arc_work[a][E.ents[w]["name"]] += 1
            for c in chars:
                wname = E.ents[c]["work"]
                if wname:
                    arc_work[a][wname] += 1
        if works and lowset:
            kws = [MEDIUM_KEYS[k] for k in MEDIUM_KEYS if k in lowset]
            for w in works:
                for m in kws:
                    work_med[w][m] += 1

    n = Counter()
    for i, d in enumerate(iter_docs(posts_path, "posts")):
        if sample and i >= sample:
            break
        n["posts"] += 1
        ts = int(d["created_utc"])
        act_posts[utc(ts).strftime("%Y-%m")] += 1
        title = d["title"]
        te, ta, _ = hits_of(title)
        be, ba, ls = hits_of(d.get("selftext") or "")
        for e in te:
            titles[e] += 1
            thread_comments[e] += d.get("num_comments") or 0
        record(te | be, ta | ba, ls, "post", ts, d.get("score") or 0)
    for i, d in enumerate(iter_docs(comments_path, "comments")):
        if sample and i >= sample * 10:
            break
        n["comments"] += 1
        ts = int(d["created_utc"])
        act_comments[utc(ts).strftime("%Y-%m")] += 1
        e, a, ls = hits_of(d.get("body") or "")
        if e or a:
            record(e, a, ls, "comment", ts, d.get("score") or 0)
        if n["comments"] % 100000 == 0:
            print(f"  pass2 comments {n['comments']:,}", flush=True)
    return dict(posts=posts, comments=comments, titles=titles, score=score_sum, year=yearc,
                first=first_ts, last=last_ts, thread=thread_comments, arc_docs=arc_docs,
                arc_score=arc_score, arc_year=arc_year, arc_char=arc_char, arc_work=arc_work,
                work_med=work_med, n=n, act_posts=act_posts, act_comments=act_comments)


# ---------------------------------------------------------------- output
def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="results")
    ap.add_argument("--sub", default="IntelligenceScaling")
    ap.add_argument("--sample", type=int, default=0, help="only use the first N posts (and 10N comments)")
    ap.add_argument("--min-arc", type=int, default=3)
    ap.add_argument("--cache", default="", help="pickle file to cache the pass-1 scan")
    ap.add_argument("--candidates-only", action="store_true", help="write candidates_review.csv and stop")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    pp = os.path.join(args.data, f"{args.sub}_posts.jsonl")
    cp = os.path.join(args.data, f"{args.sub}_comments.jsonl")
    t0 = time.time()
    print("pass 1: scanning for names ...", flush=True)
    if args.cache and os.path.exists(args.cache):
        with open(args.cache, "rb") as f:
            p1 = pickle.load(f)
    else:
        p1 = pass1(pp, cp, args.sample)
        if args.cache:
            with open(args.cache, "wb") as f:
                pickle.dump(p1, f, protocol=4)
    print(f"  done in {time.time() - t0:.0f}s: {len(p1['seqs']):,} sequences, {len(p1['vs']):,} vs-sides, "
          f"{len(p1['arcs']):,} arc candidates", flush=True)
    E = Entities()
    E, template, helpers = build(p1, E)
    generic_first = ARC_LEAD_STOP | {"video", "mind", "death", "killing", "board", "card", "chess", "real", "big", "little",
                                     "small", "great", "good", "bad", "pandemic", "read", "play", "tag", "hide", "finale",
                                     "battle", "deduction", "introduction", "swindler", "acma", "liars", "usogui"}

    def arc_ok(a):
        w = a.split()
        return len(w) >= 2 and w[0] not in generic_first and not w[0].isdigit()

    arcs_keep = {a for a, c in p1["arcs"].items() if c >= args.min_arc and arc_ok(a)}
    if args.candidates_only:
        cands = sorted((e for e in E.ents if e["kind"] == "candidate"), key=lambda e: -e["docs"])
        write_csv(os.path.join(args.out, "candidates_review.csv"), ["name", "docs", "vs_or_tag_evidence", "work_guess"],
                  [[e["name"], e["docs"], e["evidence"], e["work"]] for e in cands])
        write_csv(os.path.join(args.out, "arcs_review.csv"), ["arc", "docs"], [[a, c] for a, c in p1["arcs"].most_common() if c >= 2])
        known_works = sorted(((e["name"], e["tier"]) for e in E.ents if e["kind"] == "work"))
        print(f"candidates: {len(cands):,}; wrote review files")
        return
    print(f"build: {sum(e['kind'] == 'character' for e in E.ents):,} characters, "
          f"{sum(e['kind'] == 'work' for e in E.ents):,} works, {len(arcs_keep):,} arcs", flush=True)
    print("pass 2: counting ...", flush=True)
    r = pass2(E, arcs_keep, pp, cp, args.sample, helpers)
    print(f"  done in {time.time() - t0:.0f}s", flush=True)

    ents = E.ents

    def row_common(e):
        eid = e["id"]
        total = r["posts"][eid] + r["comments"][eid]
        return total, [total, r["posts"][eid], r["comments"][eid], r["titles"][eid],
                       round(r["score"][eid] / total, 2) if total else 0, r["thread"][eid]]

    def day(ts):
        return utc(ts).strftime("%Y-%m-%d") if ts else ""

    crow = []
    for e in ents:
        if e["kind"] != "character" or not e["aliases"]:
            continue
        total, cols = row_common(e)
        if total == 0:
            continue
        medium = e["medium"]
        crow.append([e["name"], e["work"], medium, e["tier"]] + cols +
                    [day(r["first"].get(e["id"])), day(r["last"].get(e["id"]))] +
                    [r["year"][e["id"]][y] for y in YEARS] + ["; ".join(e["aliases"][:8])])
    crow.sort(key=lambda x: -x[4])
    crow = [[i] + x for i, x in enumerate(crow, 1)]
    write_csv(os.path.join(args.out, "characters_all.csv"),
              ["rank", "character", "work", "medium", "tier", "total_mentions", "posts", "comments",
               "post_titles", "avg_score", "comments_on_threads_titled_with_them", "first_mentioned",
               "last_mentioned"] + [str(y) for y in YEARS] + ["aliases_matched"], crow)

    # works
    wrow = []
    chars_by_work = defaultdict(list)
    def nw(w):
        return re.sub(r"\s*\(.*?\)", "", w).strip().lower()

    medium_votes = defaultdict(Counter)
    for c in crow:
        if c[2]:
            chars_by_work[nw(c[2])].append((c[1], c[5]))
            for m_ in c[3].split("/"):
                medium_votes[nw(c[2])][m_] += c[5]
    for e in ents:
        if e["kind"] != "work":
            continue
        total, cols = row_common(e)
        meds = r["work_med"][e["id"]]
        medium = e["medium"] or (meds.most_common(1)[0][0] if meds else "")
        chars = sorted(chars_by_work.get(nw(e["name"]), []), key=lambda x: -x[1])
        if medium_votes.get(nw(e["name"])):
            medium = medium_votes[nw(e["name"])].most_common(1)[0][0]
        char_total = sum(x[1] for x in chars)
        if total == 0 and not chars:
            continue
        wrow.append([e["name"], medium, e["tier"], total, r["posts"][e["id"]], r["comments"][e["id"]], char_total,
                     len(chars), "; ".join(f"{n} ({c:,})" for n, c in chars[:12])])
    wrow.sort(key=lambda x: -(x[3] + x[6]))
    wrow = [[i] + x for i, x in enumerate(wrow, 1)]
    write_csv(os.path.join(args.out, "works_all.csv"),
              ["rank", "work", "medium", "source", "mentions_of_title", "posts", "comments",
               "mentions_of_its_characters", "characters_found", "top_characters"], wrow)

    # arcs
    arow = []
    for a in arcs_keep:
        n_ = r["arc_docs"][a]
        if not n_:
            continue
        works = r["arc_work"][a]
        work = ""
        if works:
            top_w, top_n = works.most_common(1)[0]
            work = top_w if top_n / sum(works.values()) >= 0.35 else ""
        chars = r["arc_char"][a].most_common(4)
        arow.append([a.title(), work, n_, round(r["arc_score"][a] / n_, 2)] +
                    [r["arc_year"][a][y] for y in YEARS] +
                    ["; ".join(f"{ents[c]['name']} ({k})" for c, k in chars)])
    arow.sort(key=lambda x: -x[2])
    arow = [[i] + x for i, x in enumerate(arow, 1)]
    write_csv(os.path.join(args.out, "arcs_all.csv"),
              ["rank", "arc_or_game", "work", "mentions", "avg_score"] + [str(y) for y in YEARS] + ["most_discussed_characters"], arow)

    # unreviewed candidates: every other capitalized phrase seen, with exact mention counts
    orows = []
    for e in ents:
        if e["kind"] != "candidate" or not e["aliases"]:
            continue
        total, cols = row_common(e)
        if total == 0:
            continue
        orows.append([e["name"], e["work"], total, cols[1], cols[2], e.get("evidence", 0)])
    orows.sort(key=lambda x: -x[2])
    orows = [[i] + x for i, x in enumerate(orows, 1)]
    write_csv(os.path.join(args.out, "names_unreviewed.csv"),
              ["rank", "name_or_term", "work_tag_seen", "mentions", "posts", "comments", "vs_or_tag_evidence"], orows)

    print(f"wrote {len(crow):,} characters, {len(wrow):,} works, {len(arow):,} arcs, {len(orows):,} unreviewed names")

    # markdown reports
    def md_row(cells):
        return "| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |"

    with open(os.path.join(args.out, "ALL_CHARACTERS.md"), "w", encoding="utf-8") as f:
        f.write(f"# Every character mentioned in r/{args.sub}\n\n"
                f"{len(crow):,} characters, ranked from most to least mentioned. Mentions = posts (title + body) plus comments "
                f"naming the character at least once, case-insensitive, covering {r['n']['posts']:,} posts and {r['n']['comments']:,} comments.\n\n"
                "**Tier:** *A (curated)* = hand-verified; *A (evidence)* = found automatically in an \"X vs Y\" title or a "
                "\"Name (Work)\" tag; *B (likely name)* = a capitalized multi-word name found only in running text (unverified).\n\n")
        f.write(md_row(["#", "Character", "Work", "Medium", "Tier", "Mentions", "Posts", "Comments", "First", "Last"] + YEARS) + "\n")
        f.write("|" + "---|" * (10 + len(YEARS)) + "\n")
        for c in crow:
            f.write(md_row([c[0], c[1], c[2], c[3], c[4], f"{c[5]:,}", f"{c[6]:,}", f"{c[7]:,}", c[11], c[12]] + [f"{v:,}" for v in c[13:13 + len(YEARS)]]) + "\n")

    with open(os.path.join(args.out, "ALL_WORKS.md"), "w", encoding="utf-8") as f:
        f.write(f"# Every novel, manga, anime, show and game mentioned\n\n{len(wrow):,} works. "
                "*Title mentions* = posts/comments naming the work; *character mentions* = mentions of its characters. "
                "Medium is inferred from words used around the title unless hand-set.\n\n")
        f.write(md_row(["#", "Work", "Medium", "Title mentions", "Character mentions", "Characters", "Top characters"]) + "\n|---|---|---|---:|---:|---:|---|\n")
        for w in wrow:
            f.write(md_row([w[0], w[1], w[2], f"{w[4]:,}", f"{w[7]:,}", w[8], w[9]]) + "\n")

    with open(os.path.join(args.out, "ARCS.md"), "w", encoding="utf-8") as f:
        f.write(f"# Arcs and games discussed\n\n{len(arow):,} arcs/games named in at least {args.min_arc} posts or comments, "
                "ranked by how often they are discussed. *Avg score* is the mean Reddit score of the posts/comments "
                "that mention the arc (a rough proxy for how well-received the discussion is).\n\n")
        f.write(md_row(["#", "Arc / game", "Work", "Mentions", "Avg score"] + YEARS + ["Most-discussed characters"]) + "\n")
        f.write("|" + "---|" * 5 + "---:|" * len(YEARS) + "---|\n")
        for a in arow:
            f.write(md_row([a[0], a[1], a[2], f"{a[3]:,}", a[4]] + [f"{v:,}" for v in a[5:5 + len(YEARS)]] + [a[5 + len(YEARS)]]) + "\n")
    import report
    report.write(args, r, crow, wrow, arow, orows, YEARS, write_csv)
    print("done in %.0fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
