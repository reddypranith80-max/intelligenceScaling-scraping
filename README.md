# r/IntelligenceScaling Scraper & Character Analysis

A full archive of the [r/IntelligenceScaling](https://www.reddit.com/r/IntelligenceScaling/) subreddit, the home of "SCD" (Smartest Character Debate), and an analysis of which characters, novels, manga, anime and shows the community argues about most.

| | |
|---|---|
| **Date range** | 10 Nov 2023 (first post) to 3 Nov 2026 |
| **Posts** | 44,007 |
| **Comments** | 704,066 |
| **Characters tracked** | 178 matched, from 108 works |
| **Most-mentioned character** | Ayanokoji Kiyotaka (*Classroom of the Elite*), 28,383 mentions |

**Full results: [results/ANALYSIS.md](results/ANALYSIS.md)**

---

## Key findings

### Top 20 characters (2023 to 2026)

Mentions = posts (title + body) and comments that name the character at least once.

| Rank | Character | Work | Mentions |
|---:|---|---|---:|
| 1 | Ayanokoji Kiyotaka | Classroom of the Elite | 28,383 |
| 2 | Light Yagami | Death Note | 28,106 |
| 3 | Baku Madarame | Usogui | 26,513 |
| 4 | Akiyama Shinichi | Liar Game | 19,371 |
| 5 | Katagiri Yuuichi | Tomodachi Game | 17,511 |
| 6 | Johan Liebert | Monster | 12,312 |
| 7 | L Lawliet | Death Note | 9,462 |
| 8 | Yokoya Norihiko | Liar Game | 9,334 |
| 9 | Fang Yuan | Reverend Insanity | 9,126 |
| 10 | Hannibal Lecter | Hannibal / Thomas Harris novels | 8,312 |
| 11 | Yumeko Jabami | Kakegurui | 6,890 |
| 12 | Akagi Shigeru | Akagi | 6,513 |
| 13 | Sherlock Holmes | Sherlock Holmes (Conan Doyle) | 6,156 |
| 14 | Patrick Jane | The Mentalist | 6,046 |
| 15 | Chen Ran | 18 Levels of Hell | 5,609 |
| 16 | Kanade Otonokoji | Super Danganronpa 2 (fan game) | 5,143 |
| 17 | Vincent Lalo | Vincent Lalo (web novel) | 4,852 |
| 18 | Yagami Takuya | Classroom of the Elite | 4,618 |
| 19 | Lelouch vi Britannia | Code Geass | 4,244 |
| 20 | Junko Enoshima | Danganronpa | 4,140 |

All 178 characters, ranked from most to least mentioned with per-year counts and first/last-seen dates, are in [results/ANALYSIS.md](results/ANALYSIS.md#all-characters-ranked) and [results/characters.csv](results/characters.csv).

### Activity by year

| Year | Posts | Comments | #1 character that year |
|---|---:|---:|---|
| 2023 (from Nov 10) | 22 | 57 | Baku Madarame |
| 2024 | 4,006 | 43,558 | Ayanokoji Kiyotaka |
| 2025 | 23,704 | 405,601 | Light Yagami |
| 2026 (to Nov 3) | 16,275 | 254,850 | Baku Madarame |

The busiest month was **March 2025**, with 2,290 posts and 49,768 comments.

### Mentions by type of work

| Medium | Works | Characters | Character mentions |
|---|---:|---:|---:|
| Manga | 28 | 45 | 129,283 |
| Light novel | 8 | 25 | 62,817 |
| Manga/Anime | 2 | 9 | 47,370 |
| Web novel | 9 | 11 | 24,167 |
| Game | 8 | 16 | 19,267 |
| TV | 14 | 16 | 14,470 |
| Novel (incl. Novel/TV) | 11 | 14 | 19,826 |
| Comic | 4 | 7 | 7,063 |
| Visual novel | 2 | 3 | 5,182 |

### Novels discussed

- **Light novels:** Classroom of the Elite, No Game No Life, Re:Zero, Roshidere, Hyouka, Durarara!!, Saga of Tanya the Evil, The Apothecary Diaries
- **Web novels:** Reverend Insanity, 18 Levels of Hell, Vincent Lalo, Lord of the Mysteries, Struggling to Survive in the Demonic Sect, Vile Dominion, Heavenly Genius, God's Imitator
- **Novels:** Sherlock Holmes, Hannibal (Thomas Harris), Dune, Star Wars Thrawn novels, Blood Meridian, The Count of Monte Cristo, The Devotion of Suspect X, the Forst series (Remigiusz Mróz), Legend of the Galactic Heroes, Romance of the Three Kingdoms
- **Visual novels:** Umineko, Zero Escape

The full breakdown of every work by medium is in [results/ANALYSIS.md](results/ANALYSIS.md#works-by-type) and [results/works_by_type.csv](results/works_by_type.csv).

---

## Repository layout

```
├── README.md
├── scraper/
│   └── scrape_subreddit.py      # downloads every post + comment (no API key needed)
├── analysis/
│   └── analyze_mentions.py      # character/work dictionary + mention counting + report
├── tools/
│   ├── package_data.py          # gzip + split raw data into <100 MB parts for GitHub
│   └── rebuild_data.py          # join the parts back into the raw .jsonl files
├── data/
│   ├── IntelligenceScaling_posts.jsonl.gz.part001
│   ├── IntelligenceScaling_comments.jsonl.gz.part001
│   └── IntelligenceScaling_comments.jsonl.gz.part002
└── results/
    ├── ANALYSIS.md              # full report
    ├── characters.csv           # all characters, ranked, with per-year counts
    ├── works_by_type.csv        # every work, its medium and its characters
    ├── works_by_title.csv       # works named directly in posts/comments
    ├── mediums.csv              # totals per medium (manga, light novel, ...)
    └── activity_by_month.csv    # posts and comments per month
```

Everything uses the Python standard library only. Python 3.11+ is required, and nothing needs `pip install`.

## Quick start

### 1. Rebuild the raw data

GitHub rejects files over 100 MB, so the archive is stored gzipped and split into parts (about 171 MB in total, 1.7 GB uncompressed). Restore it with:

```bash
python tools/rebuild_data.py
```

This writes `data/IntelligenceScaling_posts.jsonl` (222 MB) and `data/IntelligenceScaling_comments.jsonl` (1.48 GB).

### 2. Re-run the analysis

```bash
python analysis/analyze_mentions.py --data data --out results
```

It takes about 20 minutes on the full comment set. To track more characters, add them to the `CHARACTERS` list at the top of `analysis/analyze_mentions.py`, with their work, medium and aliases.

### 3. Scrape fresh data (optional)

```bash
python scraper/scrape_subreddit.py IntelligenceScaling
```

This downloads the full history from the [Arctic Shift](https://github.com/ArthurHeitmann/arctic_shift) Reddit archive, so it needs no Reddit account or API key and has no 1000-post listing cap. It writes two `.jsonl` files to the current folder. Move them into `data/`, then run `python tools/package_data.py` before committing.

## Data format

Each line is one JSON object, exactly as returned by the Reddit API.

**Posts:** `id`, `title`, `selftext`, `author`, `created_utc`, `score`, `num_comments`, `permalink`, `url`, `link_flair_text`, …

**Comments:** `id`, `body`, `author`, `created_utc`, `score`, `link_id` (the post, `t3_<post id>`), `parent_id` (the post or a parent comment, `t1_<comment id>`), …

Use `link_id` and `parent_id` to rebuild comment trees.

## How mentions are counted

- Each character has a hand-written list of aliases. Ayanokoji, for example, matches *Ayanokoji*, *Ayanokouji*, *Kiyotaka* and *Koji*.
- A post or comment counts **once per character**, however many times it names them.
- Short or ambiguous names (*Light*, *Kira*, *Joe*, *Sora*) only match when capitalised, but they can still catch unrelated words. Treat counts as approximate.
- Characters that aren't in the dictionary aren't counted.
- The character-to-work mapping was written by hand. A few works are marked *(unidentified)*.

## Notes

- This data is public Reddit content and includes usernames. It is provided for research and personal analysis. Reddit's [User Agreement](https://www.redditinc.com/policies/user-agreement) and [Data API terms](https://www.redditinc.com/policies/data-api-terms) restrict commercial use and AI-model training without permission.
- Posts or comments that were deleted before the archive captured them are missing.
