# wnscrape: web novel and light novel characters in r/IntelligenceScaling

A recheck of every web novel and light novel character named in [r/IntelligenceScaling](https://www.reddit.com/r/IntelligenceScaling/), each matched to its novel. Manga, anime, games, comics, TV and film are left out.

| | |
|---|---|
| **Date range** | 10 Nov 2023 to 13 Nov 2026 |
| **Posts** | 44,471 |
| **Comments** | 710,940 |
| **Characters** | 507 |
| **Web novel** | 264 characters in 79 novels |
| **Light novel** | 115 characters in 28 novels |
| **Other novels** | 68 characters in 22 print and classic novels |
| **Undiscovered** | 60 names whose novel could not be confirmed |

The subreddit's first post is dated 10 Nov 2023, so there is nothing earlier in November 2023 to trace. The previous archive ended on 3 Nov 2026; 464 posts and 6,874 comments were added to bring it to 13 Nov 2026.

## Files

| File | Contents |
|---|---|
| [CHARACTERS.md](CHARACTERS.md) · [csv](characters.csv) | Every character and its novel, alphabetical by novel. Web novels, light novels, other novels, then Undiscovered |
| [NOVELS.md](NOVELS.md) | Every novel with the characters found for it |
| [UNDISCOVERED.md](UNDISCOVERED.md) | Names used like characters whose novel could not be confirmed |
| [CHANGES.md](CHANGES.md) | What changed from the previous `WEB_NOVEL_CHARACTERS.md`: corrected novels, removals, merges, additions |
| [OUTLIER_CHECK.md](OUTLIER_CHECK.md) · [csv](outlier_check.csv) | Characters whose mentions come from one user or one thread; the csv has the numbers for every character |
| `data_update/` | The posts and comments added after 3 Nov 2026 (gzipped JSON lines) |
| `scripts/` | The scripts that produced these files |

## What the recheck changed

The previous list had 469 rows. Full detail is in [CHANGES.md](CHANGES.md).

| Change | Count |
|---|---:|
| Novel corrected or newly identified | 88 |
| Removed, not a novel character (terms, places, real people, titles, items, other media) | 57 |
| Spelling variants and aliases merged into the main character | 60 |
| Removed, searched but never mentioned | 58 |
| Removed, written by only one user and no novel found | 7 |
| Added | 101 |

Corrections worth knowing:

- **Being a Talent in Chusheng Demon Sect** replaces the title "Struggling to Survive in the Demonic Sect". The subreddit uses the first title about 30 times and the second once. Lu Yang, First Saint and World Honoured One belong to it as well as Ang Xiao.
- **Colonel Timo** is tagged *Solo Max-Level Newbie* in the archive, not *God's Imitator*.
- **Qin Cheng, Wang Yongxin and Cao Haichuan** move from *18 Levels of Hell* to *God's Imitator*.
- **Diwu Zhiyi** (also written Di Wu Zhi Yi, Diwu Zeyi) is one *18 Levels of Hell* character, previously split in three.
- **Mo Tan** is from *Quadruple Split*; **Gu Qingshan** from *World's Apocalypse Online*; **Feng Bujue** from *Thriller Paradise*; **Lin Qi** is the Chinese name of **Lynch** (*Blackstone Code*).
- **Shen Jihan** and **Xue Yin** are leads of stories written and posted by subreddit members, not published web novels.

## How a character gets its novel

1. **Labelled.** The name is a known character of a known novel.
2. **Tagged in the archive.** Posts write "Name (Novel)" or "Name [Novel]". Where such a tag exists it overrides any guess.
3. **Inferred from co-mentions.** For a name with no label or tag, the novel is accepted only if its title or one of its lead characters appears in at least half of the posts and comments using the name, at least 3 times, at least twice as often as the next novel, from 2 or more users with no single user writing 70% or more.
4. **Undiscovered.** Anything that fails step 3.

Ambiguous single-word names (Adam, Amon, Sora, Shiro, Lynch and others) are counted only when their novel appears in the same post, comment or thread.

## Limits

- Step 3 is evidence, not proof. Minor characters assigned to *Reverend Insanity* or *18 Levels of Hell* this way have not been checked against the novels.
- The undiscovered list still contains some names that may be original characters, typos or non-fiction names.
- Light novel coverage comes from the repo's hand-checked list plus about 70 names searched for this recheck. Minor light novel characters that nobody searched for are missing.
- Text inside images is not read, as before.

## Re-running

The scripts expect the repo cloned next to them with `data/*.jsonl` rebuilt (`python tools/rebuild_data.py`), and `REPO` set to that path.

```
python inc_scrape.py <repo>/data      # append posts/comments newer than the archive
python build_cache.py <repo>/data     # texts.pkl
python stage1.py                      # novel-title index and tokens
python stage2.py                      # match characters, find new names
python stage3.py                      # per-character statistics
python final.py <output folder>       # write every file listed above
```
