"""Writes ANALYSIS.md, mediums.csv and activity_by_month.csv from the counted results."""
import datetime
import os
from collections import Counter, defaultdict


def write(args, r, crow, wrow, arow, orows, YEARS, write_csv):
    # crow : rank, name, work, medium, tier, total, posts, comments, titles, avg, thread, first, last, years..., aliases
    # wrow : rank, work, medium, source, title_mentions, posts, comments, char_mentions, n_chars, top_chars
    # arow : rank, arc, work, mentions, avg_score, years..., characters
    out = args.out
    months = sorted(set(r["act_posts"]) | set(r["act_comments"]))
    write_csv(os.path.join(out, "activity_by_month.csv"), ["month", "posts", "comments"],
              [[m, r["act_posts"][m], r["act_comments"][m]] for m in months])
    py, cy = Counter(), Counter()
    for m in months:
        py[int(m[:4])] += r["act_posts"][m]
        cy[int(m[:4])] += r["act_comments"][m]
    busiest = max(months, key=lambda m: r["act_posts"][m] + r["act_comments"][m])

    med = defaultdict(lambda: [0, 0, 0, 0])
    for w in wrow:
        m = w[2] or "(unclassified)"
        med[m][0] += 1
        med[m][1] += w[8]
        med[m][2] += w[7]
        med[m][3] += w[4]
    mrows = sorted(([k] + v for k, v in med.items()), key=lambda x: -x[3])
    write_csv(os.path.join(out, "mediums.csv"),
              ["medium", "works", "characters", "character_mentions", "title_mentions"], mrows)

    arcs_by_work = defaultdict(list)
    for a in arow:
        if a[2]:
            arcs_by_work[a[2]].append(a)
    work_rank = sorted(wrow, key=lambda w: -(w[4] + w[7]))
    ny = len(YEARS)

    L = []
    L.append(f"# r/{args.sub}: analysis results\n")
    L.append(f"Data: **{r['n']['posts']:,} posts** and **{r['n']['comments']:,} comments**, {months[0]} to {months[-1]}. "
             f"Busiest month: **{busiest}** ({r['act_posts'][busiest]:,} posts, {r['act_comments'][busiest]:,} comments).\n")
    L.append(f"**{len(crow):,} characters** from **{len(wrow):,} works** and **{len(arow):,} arcs/games** were matched. "
             f"A further **{len(orows):,}** capitalized names and terms that could not be classified are listed in "
             f"[names_unreviewed.csv](names_unreviewed.csv), so nothing is dropped.\n")
    L.append("## Full lists\n")
    L.append("| File | What it has |\n|---|---|")
    L.append("| [ALL_CHARACTERS.md](ALL_CHARACTERS.md) / [characters_all.csv](characters_all.csv) | every character ranked high to low, with mention counts, per-year counts and first/last seen |")
    L.append("| [ALL_WORKS.md](ALL_WORKS.md) / [works_all.csv](works_all.csv) | every novel, manga, anime, show and game, with its type and characters |")
    L.append("| [ARCS.md](ARCS.md) / [arcs_all.csv](arcs_all.csv) | every arc / game discussed, ranked, with average score |")
    L.append("| [names_unreviewed.csv](names_unreviewed.csv) | every other capitalized name or term found, with mention counts (includes non-names) |")
    L.append("| [mediums.csv](mediums.csv), [activity_by_month.csv](activity_by_month.csv) | totals per type of work; posts and comments per month |\n")

    L.append("## Activity by year\n\n| Year | Posts | Comments |\n|---|---:|---:|")
    for y in YEARS:
        if py[y] or cy[y]:
            L.append(f"| {y} | {py[y]:,} | {cy[y]:,} |")
    L.append(f"| **Total** | **{sum(py.values()):,}** | **{sum(cy.values()):,}** |\n")

    L.append("## Top 50 characters\n\nMentions = posts (title + body) and comments that name the character at least once.\n")
    L.append("| # | Character | Work | Type | Mentions | " + " | ".join(str(y) for y in YEARS) + " |")
    L.append("|---:|---|---|---|---:|" + "---:|" * ny)
    for c in crow[:50]:
        L.append(f"| {c[0]} | {c[1]} | {c[2]} | {c[3]} | {c[5]:,} | " + " | ".join(f"{v:,}" for v in c[13:13 + ny]) + " |")
    L.append("\nThe full ranking is in [ALL_CHARACTERS.md](ALL_CHARACTERS.md).\n")

    L.append("## Top 10 characters per year\n")
    for k, y in enumerate(YEARS):
        top = sorted(crow, key=lambda c: -c[13 + k])[:10]
        if top and top[0][13 + k]:
            L.append(f"- **{y}:** " + ", ".join(f"{c[1]} ({c[13 + k]:,})" for c in top if c[13 + k]))
    L.append("")

    L.append("## Types of work (novels, manga, anime, shows, games)\n")
    L.append("| Type | Works | Characters | Character mentions | Title mentions |\n|---|---:|---:|---:|---:|")
    for m in mrows:
        L.append(f"| {m[0]} | {m[1]} | {m[2]} | {m[3]:,} | {m[4]:,} |")
    L.append("")
    for m in mrows:
        names = [w for w in wrow if (w[2] or "(unclassified)") == m[0]][:15]
        L.append(f"**{m[0]}** ({m[1]} works): " + ", ".join(f"{w[1]} ({w[7] + w[4]:,})" for w in names) + "\n")

    L.append("## Best arcs per work\n")
    L.append("Arcs are ranked by how often the community discusses them. *Avg score* is the mean Reddit score of the "
             "posts and comments that mention the arc, a rough proxy for how well received the discussion is.\n")
    for w in work_rank:
        lst = sorted(arcs_by_work.get(w[1], []), key=lambda a: -a[3])[:5]
        if lst:
            L.append(f"### {w[1]}\n\n| Arc | Mentions | Avg score | Most-discussed characters |\n|---|---:|---:|---|")
            for a in lst:
                L.append(f"| {a[1]} | {a[3]:,} | {a[4]} | {a[5 + ny]} |")
            L.append("")

    L.append("## Method and caveats\n")
    L.append("- Source: the Arctic Shift Reddit archive, scraped with `scraper/scrape_subreddit.py`. Text covered: post titles, post bodies and every comment. "
             "**Text inside images is not read.** About 31,000 of the 44,000 posts are images or galleries, and OCR could not be installed on the machine used.")
    L.append("- `analysis/discover_entities.py` scans all text for capitalized names, \"X vs Y\" title sides and \"Name (Work)\" tags, then counts each name case-insensitively. A post or comment counts once per character.")
    L.append("- Character-to-work labels come from a hand-checked dictionary (`analysis/analyze_mentions.py`, `analysis/reviewed_names.txt`). Names marked *(unidentified ...)* have no confirmed source, and *(ambiguous)* names are shared by several characters.")
    L.append("- Short or ambiguous names (e.g. *Light*, *Kira*, *Hal*) are matched only when capitalised, so lowercase uses are missed and a few unrelated uses are caught. Treat counts as approximate.")
    L.append("- An arc's work is inferred from the characters mentioned alongside it, and left blank when no work clearly dominates.")
    L.append(f"\n_Generated {datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d')}._\n")
    with open(os.path.join(out, "ANALYSIS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
