# r/IntelligenceScaling: Novel Characters

A full archive of [r/IntelligenceScaling](https://www.reddit.com/r/IntelligenceScaling/) (the "SCD", Smartest Character Debate, community) and a checked list of **every web novel and light novel character the subreddit talks about, each with the novel it comes from**.

| | |
|---|---|
| **Date range** | 10 Nov 2023 (the subreddit's first post) to 13 Nov 2026 |
| **Posts** | 44,474 |
| **Comments** | 710,836 |
| **Novel characters listed** | **544** |
| Web novel characters | 315, from 81 web novels |
| Community-written web fiction | 8, from 6 stories written by subreddit members |
| Light novel characters | 128, from 28 light novels |
| Other published novels | 68, from 35 novels |
| **Undiscovered** | 25 characters whose novel could not be identified |

**Start here: [results/NOVEL_CHARACTERS.md](results/NOVEL_CHARACTERS.md)**, one table with two columns: character and novel.

The lists are not ranked. A character is on the list if the archive mentions it at all, and each one was checked against what the posts and comments themselves say it is from. What the recheck changed is in [results/CHANGES.md](results/CHANGES.md).

## Files

| File | Contents |
|---|---|
| [results/NOVEL_CHARACTERS.md](results/NOVEL_CHARACTERS.md) · [csv](results/novel_characters.csv) | **Every character and its novel** in one table |
| [results/WEB_NOVEL_CHARACTERS.md](results/WEB_NOVEL_CHARACTERS.md) · [csv](results/web_novel_characters.csv) | Web novel characters, grouped by novel (Chinese, Korean and Western web novels, plus the stories written by subreddit members) |
| [results/LIGHT_NOVEL_CHARACTERS.md](results/LIGHT_NOVEL_CHARACTERS.md) · [csv](results/light_novel_characters.csv) | Light novel characters, grouped by novel |
| [results/OTHER_NOVEL_CHARACTERS.md](results/OTHER_NOVEL_CHARACTERS.md) · [csv](results/other_novel_characters.csv) | Characters from other published novels (Sherlock Holmes, Dune, Hannibal Lecter novels ...) |
| [results/UNDISCOVERED_CHARACTERS.md](results/UNDISCOVERED_CHARACTERS.md) · [csv](results/undiscovered_characters.csv) | **Undiscovered:** characters whose novel could not be found |
| [results/NOVELS.md](results/NOVELS.md) | Every novel, by type |
| [results/CHANGES.md](results/CHANGES.md) | What the recheck changed: wrong novels corrected, outliers removed, characters and novels added |
| [results/novel_characters_evidence.csv](results/novel_characters_evidence.csv) | The numbers behind each entry (mentions, first and last date, how often the novel is named alongside). Kept separate so the lists stay at two fields |

Every csv list has exactly two columns: `character`, `novel`.

## What is in the lists

**Novels with the most characters discussed**

| Web novels | Characters | | Light novels | Characters |
|---|---:|---|---|---:|
| Reverend Insanity | 73 | | Classroom of the Elite | 52 |
| 18 Levels of Hell: Lying Is Forbidden Here | 62 | | No Game No Life | 14 |
| Lord of the Mysteries | 24 | | Re:Zero | 13 |
| Vile Dominion | 17 | | Overlord | 6 |
| Being a Talent in Chusheng Demon Sect | 11 | | Hyouka | 4 |
| God's Imitator | 11 | | Roshidere | 4 |
| Shadow Slave | 7 | | The Apothecary Diaries | 4 |
| Worm | 7 | | Monogatari | 4 |

**Undiscovered.** 25 characters are discussed as novel characters but have no novel that could be confirmed: Bai Ding Zhe, Bai Yu, Bai Zhe, Chen Changsheng, Chen Jie, Devil Advisor, Duan Lou, Gao Chuan, Gu Shiyan, Heiti Taizheng, Jiang Shen, Lin Yu, Long Chian, Ocrevius, Qi Jia, Ro Zha, Sou Loang, Tan Mo, Tarantulian Demon, The Founder, Vereiya, Wang Wei, Xie Wuming, Zha Hiangtan, Zi Chen. For most of them the subreddit itself asks "where is he from?" and gets no answer, or the novel is untranslated or deliberately kept private.

**Community-written web fiction.** Six stories were written by subreddit members and are debated like any other novel: *An Ordinary Path through an Incredulous Life* (Shen Jihan), *The Endless Food Chain* (Xue Yin, Li Guang), *Kei and Satoshi*, *Endless Wonders* (Xuan Luo), *The Paradoxical Miracle* (Luther Roy) and *The Blind Observer* (Charles Morris). They are listed at the end of the web novel file.

## What the recheck changed

Full details are in [results/CHANGES.md](results/CHANGES.md). In short:

- **Coverage.** The archive in the repository ended on 3 Nov 2026, not 11 Nov. It now runs to 13 Nov 2026 (+467 posts, +6,770 comments). Nothing exists before 10 Nov 2023 because that is the day of the subreddit's first post.
- **More than 20 characters were under the wrong novel**, for example Colonel Timo (listed under God's Imitator, actually Solo Max-Level Newbie), "Lin Qi" (listed under 18 Levels of Hell, actually Lynch from Blackstone Code) and Feng Bujue (actually Thriller Paradise).
- **About 60 "unidentified" characters now have a novel**, for example Lu Yang (Being a Talent in Chusheng Demon Sect), Mo Tan (Quadruple Split), Ning Yu (The Cicada's Song Accompanies Yangxi) and Gu Chensha (Dragon Talisman).
- **Outliers removed.** Items, places and terms that had been counted as characters (Wisdom Gu, Heavenly Court, Gui Yu ...); names that belong to manga, manhua or real people; the 54 characters that were listed with 0 mentions; and misleading matches such as Kirito (mostly Kirito Kamui from Psycho-Pass) and "Linley" (a typo of "likely").
- **The Three Kingdoms strategists** (Zhuge Liang, Guo Jia, Sima Yi ...) are no longer listed as novel characters, because the subreddit discusses them as characters of the manhua *The Ravages of Time* about nine times out of ten.
- **Added:** about 35 novels and 90 web novel characters that were missing, and a separate light novel list.

## Other media

The earlier all-media analysis (manga, anime, TV, games, comics, ranked by mentions) is still in `results/` and was re-run on the updated archive with the corrected labels, but it is not the focus of this repository:
[ANALYSIS.md](results/ANALYSIS.md), [ALL_CHARACTERS.md](results/ALL_CHARACTERS.md) (564 characters), [ALL_WORKS.md](results/ALL_WORKS.md) (225 works), [ARCS.md](results/ARCS.md) (255 arcs), `names_unreviewed.csv` (18,581 other capitalized names and terms), `mediums.csv` and `activity_by_month.csv`.

## Repository layout

```
├── README.md
├── scraper/scrape_subreddit.py     # downloads every post + comment (no API key); --update adds only what is new
├── analysis/
│   ├── novel_catalog.txt           # hand-checked: novel, type, character, spellings
│   ├── novel_characters.py         # checks the catalog against the archive, writes the novel lists
│   ├── discover_entities.py        # all-media analysis: finds names, counts them, writes the ranked reports
│   ├── report.py                   # writes ANALYSIS.md
│   ├── analyze_mentions.py         # seed dictionary for the all-media analysis
│   ├── reviewed_names.txt          # extra hand-checked names for the all-media analysis
│   └── reviewed_names.py           # loader for the file above
├── tools/
│   ├── package_data.py             # gzip + split raw data into <100 MB parts for GitHub
│   └── rebuild_data.py             # join the parts back into .jsonl
├── data/                           # raw archive, gzipped and split
└── results/                        # every list and report
```

Standard library only, Python 3.11+.

## Quick start

```bash
python tools/rebuild_data.py                 # restore data/*.jsonl (about 1.7 GB)
python analysis/novel_characters.py          # write the novel character lists (about 1.5 minutes)
```

To bring the archive up to date first:

```bash
python scraper/scrape_subreddit.py IntelligenceScaling --update data   # fetch only what is newer
python tools/package_data.py                                           # re-split before committing
```

The all-media reports are rebuilt with `python analysis/discover_entities.py --data data --out results` (about 4 minutes).

## How it works

1. **Catalog.** `analysis/novel_catalog.txt` lists each novel with its type, and each character with the spellings the subreddit uses (for example *Diwu Zhiyi / Di Wu Zhi Yi*). Candidates came from scanning every capitalized name in the archive and measuring which novel each one is mentioned next to; each link was then confirmed by reading what the posts say ("X from Y", "X (Y)", "the MC of Y").
2. **Check.** `novel_characters.py` reads every post title, post body and comment and looks for each spelling as whole words. Longer names win, so "Hei Lou Lan" is never counted as "Lou Lan".
3. **Outlier guard.** Names that are also ordinary words or belong to several series (Adam, Amon, Shiro, Lynch, Kirito, Kei ...) count only when their novel, or another character of it, is named in the same post or comment, or in the post the comment belongs to.
4. **List.** Characters with at least one confirmed mention are written to the lists. Catalog entries the archive never mentions are left out and printed at the end of the run.

To add a character, add one line to the catalog and run the script again.

## Limitations

- **Images are not read.** About 31,000 of the 44,000 posts are images or galleries, and text inside them (tier lists, stat sheets) is not covered. Titles, post bodies and all comments are.
- **Rare characters can be missed.** A character has to be in the catalog to be listed. The catalog covers every name found by the scan that could be tied to a novel, but a character mentioned once or twice under an unusual spelling may not be in it.
- **Translated names vary.** Chinese and Korean web novels often have several English titles and spellings. The lists use the form the subreddit uses most.
- **Type is a judgement call.** A work is filed by its original form: web novels that later became manhwa or anime stay under web novels; visual novels, manga and their novelisations are left out.
- **Undiscovered means unconfirmed, not unknowable.** Some of those novels exist but are untranslated or were never named in the subreddit.

## Notes

- This is public Reddit content and includes usernames. It is provided for research and personal analysis. Reddit's [User Agreement](https://www.redditinc.com/policies/user-agreement) and [Data API terms](https://www.redditinc.com/policies/data-api-terms) restrict commercial use and AI-model training without permission.
- Posts and comments deleted before the archive captured them are missing.
