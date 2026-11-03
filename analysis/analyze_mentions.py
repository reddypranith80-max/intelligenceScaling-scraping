"""Count character / work mentions in the scraped r/IntelligenceScaling archive.

Usage: python analysis/analyze_mentions.py [--data data] [--out results]
Reads data/IntelligenceScaling_posts.jsonl and data/IntelligenceScaling_comments.jsonl
(run tools/rebuild_data.py first if you only have the .gz parts).
Writes CSVs and ANALYSIS.md into the output folder.
"""
import argparse
import csv
import datetime
import heapq
import json
import os
import re
from collections import Counter, defaultdict

# name, work, medium, aliases ("!" prefix = case-sensitive, otherwise case-insensitive)
CHARACTERS = [
    # Usogui
    ("Baku Madarame", "Usogui", "Manga", ["Baku Madarame", "Madarame", "Baku"]),
    ("Kiruma Souichi", "Usogui", "Manga", ["Kiruma Souichi", "Souichi Kiruma", "Kiruma"]),
    ("Kaji Takaomi", "Usogui", "Manga", ["Kaji Takaomi", "!Kaji"]),
    ("Suteguma Satoru", "Usogui", "Manga", ["Suteguma"]),
    ("Gonen", "Usogui", "Manga", ["!Gonen"]),
    # Liar Game
    ("Akiyama Shinichi", "Liar Game", "Manga", ["Akiyama", "Shinchi Akiyama", "Akiyama Shinchi"]),
    ("Yokoya Norihiko", "Liar Game", "Manga", ["Yokoya"]),
    ("Kimura Kei", "Liar Game", "Manga", ["Kimura Kei", "Kei Kimura"]),
    ("Fukunaga Yuji", "Liar Game", "Manga", ["Fukunaga"]),
    ("Kanzaki Nao", "Liar Game", "Manga", ["Kanzaki Nao", "Nao Kanzaki"]),
    # Akagi
    ("Akagi Shigeru", "Akagi", "Manga", ["Akagi Shigeru", "Shigeru Akagi", "Akagi"]),
    ("Washizu Iwao", "Akagi", "Manga", ["Washizu"]),
    # Classroom of the Elite
    ("Ayanokoji Kiyotaka", "Classroom of the Elite", "Light novel", ["Ayanokoji", "Ayanokouji", "Ayanakoji", "Ayanokji", "Kiyotaka", "!Koji", "Ayano"]),
    ("Horikita Manabu", "Classroom of the Elite", "Light novel", ["Manabu"]),
    ("Horikita Suzune", "Classroom of the Elite", "Light novel", ["Suzune"]),
    ("Sakayanagi Arisu", "Classroom of the Elite", "Light novel", ["Sakayanagi"]),
    ("Ryuen Kakeru", "Classroom of the Elite", "Light novel", ["Ryuen"]),
    ("Nagumo Miyabi", "Classroom of the Elite", "Light novel", ["Nagumo"]),
    ("Kushida Kikyou", "Classroom of the Elite", "Light novel", ["Kushida"]),
    ("Amasawa Ichika", "Classroom of the Elite", "Light novel", ["Ichika", "Amasawa"]),
    ("Ichinose Honami", "Classroom of the Elite", "Light novel", ["Ichinose"]),
    ("Koenji Rokusuke", "Classroom of the Elite", "Light novel", ["Koenji"]),
    ("Yagami Takuya", "Classroom of the Elite", "Light novel", ["Takuya Yagami", "Yagami Takuya", "!Takuya"]),
    ("Tsukishiro", "Classroom of the Elite", "Light novel", ["Tsukishiro"]),
    ("Ayanokoji Atsuomi", "Classroom of the Elite", "Light novel", ["Atsuomi"]),
    # Tomodachi Game
    ("Katagiri Yuuichi", "Tomodachi Game", "Manga", ["Yuuichi", "Yuiichi", "Yuichi", "Katagiri"]),
    ("Mikasa Tenji", "Tomodachi Game", "Manga", ["Tenji Mikasa", "Mikasa Tenji"]),
    # Death Note
    ("Light Yagami", "Death Note", "Manga/Anime", ["Light Yagami", "Yagami Light", "!Light", "!Kira", "Fent Yagami"]),
    ("L Lawliet", "Death Note", "Manga/Anime", ["L Lawliet", "Lawliet", "CTW L", "Canon L", "Cannon L", "Animanga L", "!L's", "vs L\\b", "\\bL vs"]),
    ("Near (Nate River)", "Death Note", "Manga/Anime", ["Nate River", "Mt Near"]),
    ("Mello", "Death Note", "Manga/Anime", ["!Mello"]),
    ("Beyond Birthday", "Death Note", "Manga/Anime", ["Beyond Birthday"]),
    ("Naomi Misora", "Death Note", "Manga/Anime", ["Naomi Misora"]),
    ("Minoru Tanaka", "Death Note", "Manga/Anime", ["Minoru Tanaka"]),
    # Mentalist
    ("Patrick Jane", "The Mentalist", "TV", ["Patrick Jane", "!Jane"]),
    ("Red John", "The Mentalist", "TV", ["Red John"]),
    # Monster
    ("Johan Liebert", "Monster", "Manga", ["Johan", "Liebert"]),
    # Hannibal
    ("Hannibal Lecter", "Hannibal / Thomas Harris novels", "Novel/TV", ["Hannibal", "Lecter"]),
    ("Will Graham", "Hannibal / Thomas Harris novels", "Novel/TV", ["Will Graham"]),
    ("Francis Dolarhyde", "Hannibal / Thomas Harris novels", "Novel/TV", ["Dolarhyde"]),
    # Reverend Insanity & Chinese web novels
    ("Fang Yuan", "Reverend Insanity", "Web novel", ["Fang Yuan"]),
    ("Chen Ran", "18 Levels of Hell", "Web novel", ["Chen Ran"]),
    ("Ang Xiao", "Struggling to Survive in the Demonic Sect", "Web novel", ["Ang Xiao"]),
    ("Niu Youdao", "Heavenly Genius", "Web novel", ["Niu Youdao"]),
    ("Lin Sizhi", "God's Imitator", "Web novel", ["Lin Sizhi"]),
    ("Cai Zhiyuan", "God's Imitator", "Web novel", ["Cai Zhiyuan", "Cai Zhuyuan"]),
    ("Li Gang", "Vile Dominion", "Web novel", ["Li Gang"]),
    ("Xue Yin", "(unidentified web novel)", "Web novel", ["Xue Yin"]),
    ("Shen Jihan", "(unidentified web novel)", "Web novel", ["Shen Jihan"]),
    ("Lu Bu", "Romance of the Three Kingdoms", "Classic novel", ["Lu Bu"]),
    ("Zhuge Liang", "Romance of the Three Kingdoms", "Classic novel", ["Zhuge Liang"]),
    ("Guo Jia", "Romance of the Three Kingdoms", "Classic novel", ["Guo Jia"]),
    ("Sima Yi", "Romance of the Three Kingdoms", "Classic novel", ["Sima Yi"]),
    # Other novels
    ("Vincent Lalo", "Usogui", "Manga", ["Vincent Lalo", "Vincent Laur", "!Lalo"]),
    ("Klein Moretti", "Lord of the Mysteries", "Web novel", ["Klein Moretti", "!Klein"]),
    ("Paul Atreides", "Dune", "Novel", ["Paul Atreides", "Leto II"]),
    ("Medea Solon", "Your Throne", "Webtoon/novel", ["Medea Solon"]),
    ("Wiktor Forst", "Forst series (Remigiusz Mroz)", "Novel", ["Wiktor Forst", "Trawers", "Ekspozycja"]),
    ("Iwo Eliasz", "Forst series (Remigiusz Mroz)", "Novel", ["Iwo Eliasz"]),
    ("Luther Roy", "(community-made novel)", "Novel", ["Luther Roy"]),
    ("Tanya Degurechaff", "Saga of Tanya the Evil", "Light novel", ["Tanya"]),
    ("Reinhard von Lohengramm", "Legend of the Galactic Heroes", "Novel", ["Lohengramm"]),
    ("Grand Admiral Thrawn", "Star Wars (Thrawn novels)", "Novel", ["Thrawn"]),
    ("Maomao", "The Apothecary Diaries", "Light novel", ["Maomao"]),
    ("Oreki Houtarou", "Hyouka", "Light novel", ["Oreki"]),
    ("Ishigami Tetsuya", "The Devotion of Suspect X", "Novel", ["Ishigami Tetsuya"]),
    ("Kuze Masachika", "Roshidere", "Light novel", ["Kuze"]),
    ("Riku Dola", "No Game No Life", "Light novel", ["Riku"]),
    ("Sora (NGNL)", "No Game No Life", "Light novel", ["!Sora"]),
    ("Shiro (NGNL)", "No Game No Life", "Light novel", ["!Shiro"]),
    ("Schwi Dola", "No Game No Life", "Light novel", ["Schwi"]),
    ("Jibril", "No Game No Life", "Light novel", ["Jibril"]),
    ("Subaru Natsuki", "Re:Zero", "Light novel", ["Subaru"]),
    ("Echidna", "Re:Zero", "Light novel", ["Echidna"]),
    ("Kyoko Kirigiri / Danganronpa cast", "Danganronpa", "Game/Novel", ["Kirigiri"]),
    ("Junko Enoshima", "Danganronpa", "Game", ["Junko"]),
    ("Nagito Komaeda", "Danganronpa", "Game", ["Nagito", "Komaeda"]),
    ("Kokichi Ouma", "Danganronpa", "Game", ["Kokichi", "Kokichi Oma"]),
    ("Makoto Naegi", "Danganronpa", "Game", ["Naegi"]),
    ("Izuru Kamukura", "Danganronpa", "Game", ["Izuru"]),
    ("Shuichi Saihara", "Danganronpa", "Game", ["Saihara"]),
    ("Celestia Ludenberg", "Danganronpa", "Game", ["Celestia"]),
    ("Kanade Otonokoji", "Super Danganronpa 2 (fan)", "Game", ["Kanade"]),
    # Umineko / Zero Escape
    ("Beatrice", "Umineko", "Visual novel", ["!Beatrice"]),
    ("Battler Ushiromiya", "Umineko", "Visual novel", ["Battler"]),
    ("Akane Kurashiki", "Zero Escape", "Visual novel", ["Akane Kurashiki", "!Akane"]),
    # Kakegurui
    ("Yumeko Jabami", "Kakegurui", "Manga", ["Yumeko"]),
    ("Mary Saotome", "Kakegurui", "Manga", ["Mary Saotome", "!Mary"]),
    ("Kirari Momobami", "Kakegurui", "Manga", ["Kirari"]),
    ("Ririka Momobami", "Kakegurui", "Manga", ["Ririka"]),
    ("Terano Totobami", "Kakegurui", "Manga", ["Terano"]),
    # Code Geass etc anime
    ("Lelouch vi Britannia", "Code Geass", "Anime", ["Lelouch"]),
    ("Dazai Osamu", "Bungo Stray Dogs", "Manga/Anime", ["Dazai"]),
    ("Fyodor Dostoevsky", "Bungo Stray Dogs", "Manga/Anime", ["Fyodor"]),
    ("Senku Ishigami", "Dr. Stone", "Manga", ["Senku", "Ishigami"]),
    ("Chishiya Shuntaro", "Alice in Borderland", "Manga/TV", ["Chishiya"]),
    ("Arisu Ryohei", "Alice in Borderland", "Manga/TV", ["Ryohei"]),
    ("Aqua Hoshino", "Oshi no Ko", "Manga", ["Aqua Hoshino", "!Aqua"]),
    ("Makima", "Chainsaw Man", "Manga", ["Makima"]),
    ("Kenjaku", "Jujutsu Kaisen", "Manga", ["Kenjaku"]),
    ("Sukuna", "Jujutsu Kaisen", "Manga", ["Sukuna"]),
    ("Aizen Sosuke", "Bleach", "Manga", ["Aizen"]),
    ("Muzan Kibutsuji", "Demon Slayer", "Manga", ["Muzan"]),
    ("Meruem", "Hunter x Hunter", "Manga", ["Meruem"]),
    ("Chrollo Lucilfer", "Hunter x Hunter", "Manga", ["Chrollo"]),
    ("Itachi Uchiha", "Naruto", "Manga", ["Itachi"]),
    ("Shikamaru Nara", "Naruto", "Manga", ["Shikamaru"]),
    ("Gintoki Sakata", "Gintama", "Manga", ["Gintoki"]),
    ("Kaiji Itou", "Kaiji", "Manga", ["!Kaiji"]),
    ("Isagi Yoichi", "Blue Lock", "Manga", ["Isagi"]),
    ("Furuta Nimura", "Tokyo Ghoul", "Manga", ["Furuta"]),
    ("Midori / Shin", "Your Turn to Die", "Game", ["Midori"]),
    ("Nana Hiiragi", "Munou na Nana", "Manga", ["Nana Hiiragi"]),
    ("Yuno Gasai", "Future Diary", "Manga", ["Yuno Gasai"]),
    ("Izaya Orihara", "Durarara!!", "Light novel", ["Izaya"]),
    ("Eren Yeager", "Attack on Titan", "Manga", ["Eren"]),
    ("Griffith", "Berserk", "Manga", ["Griffith"]),
    ("Goku", "Dragon Ball", "Manga", ["Goku"]),
    ("Joseph Joestar", "JoJo's Bizarre Adventure", "Manga", ["Joseph Joestar"]),
    ("Conan Edogawa / Shinichi Kudo", "Detective Conan", "Manga", ["Conan", "Kudo Shinichi", "Shinichi Kudo"]),
    ("Kaito Kid", "Magic Kaito", "Manga", ["Kaito Kid", "Kaitou Kid"]),
    ("Ron Kamonohashi", "Ron Kamonohashi's Forbidden Deductions", "Manga", ["Ron Kamonohashi"]),
    ("William James Moriarty", "Moriarty the Patriot", "Manga", ["William James Moriarty", "!WJM"]),
    ("Moriarty (BBC/other)", "Sherlock Holmes", "Novel/TV", ["Jim Moriarty", "Moriarty"]),
    ("Sherlock Holmes", "Sherlock Holmes (Conan Doyle novels)", "Novel", ["Sherlock", "Holmes"]),
    ("Phoenix Wright", "Ace Attorney", "Game", ["Phoenix Wright"]),
    ("Manfred von Karma", "Ace Attorney", "Game", ["Von Karma"]),
    ("Batman", "DC Comics", "Comic", ["Batman", "Bruce Wayne"]),
    ("The Joker", "DC Comics", "Comic", ["!Joker"]),
    ("The Riddler", "DC Comics", "Comic", ["Riddler"]),
    ("Eobard Thawne", "DC Comics", "Comic", ["Thawne"]),
    ("John Constantine", "Hellblazer / DC", "Comic", ["Constantine"]),
    ("Lucifer Morningstar", "Lucifer", "TV/Comic", ["Lucifer"]),
    ("Ozymandias", "Watchmen", "Comic", ["Ozymandias"]),
    ("Loki", "Marvel", "Comic/Film", ["!Loki"]),
    ("Doctor Doom", "Marvel", "Comic", ["Doctor Doom", "Dr Doom"]),
    ("Tony Stark", "Marvel", "Comic/Film", ["Tony Stark"]),
    ("Homelander", "The Boys", "TV/Comic", ["Homelander"]),
    ("Rick Sanchez", "Rick and Morty", "TV", ["Rick Sanchez"]),
    ("Dexter Morgan", "Dexter", "TV/Novel", ["Dexter"]),
    ("Brian Moser", "Dexter", "TV", ["Brian Moser"]),
    ("Joe Goldberg", "You", "TV/Novel", ["Joe Goldberg", "!Joe"]),
    ("Michael Scofield", "Prison Break", "TV", ["Scofield"]),
    ("Walter White", "Breaking Bad", "TV", ["Walter White", "Heisenberg"]),
    ("Saul Goodman", "Better Call Saul", "TV", ["Saul Goodman", "Jimmy McGill"]),
    ("Gustavo Fring", "Breaking Bad", "TV", ["Gus Fring", "Gustavo Fring"]),
    ("John Kramer (Jigsaw)", "Saw", "Film", ["Jigsaw", "John Kramer"]),
    ("Mark Hoffman", "Saw", "Film", ["Hoffman"]),
    ("William Afton", "Five Nights at Freddy's", "Game", ["Afton"]),
    ("Gregory House", "House M.D.", "TV", ["Gregory House", "Dr House", "Dr. House"]),
    ("Raymond Reddington", "The Blacklist", "TV", ["Reddington"]),
    ("Frank Abagnale Jr.", "Catch Me If You Can", "Film/Memoir", ["Abagnale"]),
    ("Edmond Dantes", "The Count of Monte Cristo", "Novel", ["Dantes", "Dantès"]),
    ("Assane Diop", "Lupin", "TV", ["Assane"]),
    ("Judge Holden", "Blood Meridian", "Novel", ["Judge Holden"]),
    ("Rust Cohle", "True Detective", "TV", ["Rust Cohle"]),
    ("Anton Chigurh", "No Country for Old Men", "Novel/Film", ["Chigurh"]),
    ("Hans Landa", "Inglourious Basterds", "Film", ["Hans Landa"]),
    ("Tony Soprano", "The Sopranos", "TV", ["Tony Soprano"]),
    ("Sheldon Cooper", "The Big Bang Theory", "TV", ["Sheldon Cooper"]),
    ("Shawn Spencer", "Psych", "TV", ["Shawn Spencer"]),
    ("Columbo", "Columbo", "TV", ["Columbo"]),
    ("Tyler Durden", "Fight Club", "Novel/Film", ["Tyler Durden"]),
    ("Brian Finch", "Limitless", "Novel/Film/TV", ["Brian Finch"]),
    ("Emperor Palpatine", "Star Wars", "Film", ["Palpatine"]),
    ("Apollyon", "For Honor", "Game", ["Apollyon"]),
    ("Murphy Lawden", "SCP Foundation", "Online fiction", ["Murphy Lawden"]),
    ("Seonghyun Moon (Dr. Frost)", "Dr. Frost", "Webtoon", ["Seonghyun Moon", "Dr Frost"]),
    ("Suji Seong / Nambong Baek", "Pyramid Game", "Webtoon", ["Suji Seong", "Nambong"]),
    ("Oberon Vortigern", "Fate/Grand Order", "Game", ["Oberon"]),
    ("Daybit Sem Void", "Fate/Grand Order", "Game", ["Daybit"]),
    ("Otto Apocalypse", "Honkai Impact 3rd", "Game", ["Otto Apocalypse"]),
    ("Melvina", "Melvina's Therapy", "Webtoon", ["Melvina"]),
    ("Magnus Carlsen", "(real person)", "Real life", ["Carlsen"]),
    ("John von Neumann", "(real person)", "Real life", ["Von Neumann"]),
    ("Napoleon Bonaparte", "(real person)", "Real life", ["Napoleon"]),
    ("Nikola Tesla", "(real person)", "Real life", ["Tesla"]),
    ("Einstein", "(real person)", "Real life", ["Einstein"]),
]

WORKS = [
    ("Death Note", ["Death Note"]),
    ("Liar Game", ["Liar Game"]),
    ("Usogui", ["Usogui", "Lie Eater"]),
    ("Tomodachi Game", ["Tomodachi Game"]),
    ("Classroom of the Elite", ["Classroom of the Elite", "!COTE", "Youkoso Jitsuryoku"]),
    ("Reverend Insanity", ["Reverend Insanity"]),
    ("Kakegurui", ["Kakegurui"]),
    ("Danganronpa", ["Danganronpa"]),
    ("Code Geass", ["Code Geass"]),
    ("The Mentalist", ["Mentalist"]),
    ("Monster (Urasawa)", ["!Monster"]),
    ("Sherlock Holmes", ["Sherlock"]),
    ("Detective Conan", ["Detective Conan", "Case Closed"]),
    ("Kaiji", ["!Kaiji"]),
    ("Akagi", ["Akagi"]),
    ("Umineko", ["Umineko"]),
    ("Zero Escape", ["Zero Escape"]),
    ("No Game No Life", ["No Game No Life", "!NGNL"]),
    ("Lord of the Mysteries", ["Lord of the Mysteries", "!LOTM"]),
    ("Alice in Borderland", ["Alice in Borderland"]),
    ("Squid Game", ["Squid Game"]),
    ("Dr. Stone", ["Dr\\.? ?Stone"]),
    ("Oshi no Ko", ["Oshi no Ko"]),
    ("Bungo Stray Dogs", ["Bungou? Stray Dogs", "!BSD"]),
    ("Re:Zero", ["Re:? ?Zero"]),
    ("Fate series", ["Fate/", "Fate Grand Order", "!FGO"]),
    ("Breaking Bad / Better Call Saul", ["Breaking Bad", "Better Call Saul"]),
    ("Dexter", ["Dexter"]),
    ("You (Netflix/novels)", ["!You Netflix", "Joe Goldberg"]),
    ("Prison Break", ["Prison Break"]),
    ("Saw", ["!Saw\\b"]),
    ("Dune", ["Dune"]),
    ("Fight Club", ["Fight Club"]),
    ("Hyouka", ["Hyouka"]),
    ("Roshidere", ["Roshidere"]),
    ("SCP Foundation", ["!SCP"]),
    ("Pyramid Game", ["Pyramid Game"]),
    ("Dr. Frost", ["Dr\\.? Frost"]),
    ("Your Turn to Die", ["Your Turn to Die", "!YTTD"]),
    ("Moriarty the Patriot", ["Moriarty the Patriot"]),
    ("Ace Attorney", ["Ace Attorney"]),
    ("Tokyo Ghoul", ["Tokyo Ghoul"]),
    ("Hunter x Hunter", ["Hunter x Hunter", "!HxH"]),
    ("Jujutsu Kaisen", ["Jujutsu Kaisen", "!JJK"]),
    ("Kyokou Suiri", ["Kyokou Suiri", "In/Spectre"]),
    ("Chainsaw Man", ["Chainsaw Man"]),
    ("Blue Lock", ["Blue Lock"]),
    ("Gintama", ["Gintama"]),
    ("Honkai Impact", ["Honkai"]),
    ("Lupin", ["!Lupin"]),
    ("Munou na Nana", ["Munou na Nana"]),
    ("Reverend Insanity / Chinese web novels", ["Gu Zhen Ren", "Spring Autumn Cicada"]),
    ("18 Levels of Hell", ["18 Levels of Hell", "Eighteen Levels of Hell"]),
    ("Monte Cristo", ["Monte Cristo"]),
    ("Romance of the Three Kingdoms", ["Three Kingdoms", "!ROTK"]),
]


def alt(aliases):
    out = []
    for a in sorted(aliases, key=len, reverse=True):
        if a.startswith("!"):
            out.append(r"\b" + a[1:] + r"(?!\w)" if not a.endswith("\\b") else r"\b" + a[1:])
        else:
            out.append(r"(?i:\b" + a + r"(?!\w))")
    return "|".join(out)


def build(entries, alias_index):
    parts = []
    for i, e in enumerate(entries):
        parts.append(f"(?P<g{i}>{alt(e[alias_index])})")
    return re.compile("|".join(parts))


def hits(rx, text):
    return {int(m.lastgroup[1:]) for m in rx.finditer(text)}


def utc(ts):
    return datetime.datetime.fromtimestamp(int(ts), datetime.UTC)


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def md_escape(s):
    return s.replace("|", "\\|").replace("\n", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="results")
    ap.add_argument("--sub", default="IntelligenceScaling")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    posts_path = os.path.join(args.data, f"{args.sub}_posts.jsonl")
    comments_path = os.path.join(args.data, f"{args.sub}_comments.jsonl")

    char_rx = build(CHARACTERS, 3)
    work_rx = build(WORKS, 1)
    nw = len(WORKS)
    c_post = Counter(); c_title = Counter(); c_thread = Counter(); c_comm = Counter()
    w_post = Counter(); w_title = Counter(); w_thread = Counter(); w_comm = Counter()
    c_year = defaultdict(Counter)       # character -> year -> mentions
    c_first, c_last = {}, {}
    posts_month = Counter(); comments_month = Counter()
    top_posts = []                      # heap of (num_comments, title, date, permalink)
    ts_lo, ts_hi = None, None

    def seen(i, ts):
        c_year[i][utc(ts).year] += 1
        if i not in c_first or ts < c_first[i]:
            c_first[i] = ts
        if i not in c_last or ts > c_last[i]:
            c_last[i] = ts

    npost = 0
    with open(posts_path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            npost += 1
            ts = int(d["created_utc"])
            ts_lo = ts if ts_lo is None else min(ts_lo, ts)
            ts_hi = ts if ts_hi is None else max(ts_hi, ts)
            posts_month[utc(ts).strftime("%Y-%m")] += 1
            ncom = d.get("num_comments") or 0
            item = (ncom, d["title"], utc(ts).strftime("%Y-%m-%d"), d.get("permalink", ""))
            if len(top_posts) < 25:
                heapq.heappush(top_posts, item)
            else:
                heapq.heappushpop(top_posts, item)
            title = d["title"]
            body = title + "\n" + (d.get("selftext") or "")
            for i in hits(char_rx, body):
                c_post[i] += 1
                seen(i, ts)
            for i in hits(char_rx, title):
                c_title[i] += 1
                c_thread[i] += ncom
            for i in hits(work_rx, body):
                w_post[i] += 1
            for i in hits(work_rx, title):
                w_title[i] += 1
                w_thread[i] += ncom

    ncomm = 0
    with open(comments_path, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            ncomm += 1
            ts = int(d["created_utc"])
            ts_lo, ts_hi = min(ts_lo, ts), max(ts_hi, ts)
            comments_month[utc(ts).strftime("%Y-%m")] += 1
            body = d.get("body") or ""
            for i in hits(char_rx, body):
                c_comm[i] += 1
                seen(i, ts)
            for i in hits(work_rx, body):
                w_comm[i] += 1

    years = list(range(utc(ts_lo).year, utc(ts_hi).year + 1))
    day = lambda ts: utc(ts).strftime("%Y-%m-%d") if ts else ""

    # characters, ranked by total mentions (highest first)
    rows = []
    for i, (name, work, medium, _) in enumerate(CHARACTERS):
        total = c_post[i] + c_comm[i]
        if total == 0:
            continue
        rows.append([name, work, medium, total, c_post[i], c_comm[i], c_title[i], c_thread[i],
                     day(c_first.get(i)), day(c_last.get(i))] + [c_year[i][y] for y in years])
    rows.sort(key=lambda r: -r[3])
    rows = [[n] + r for n, r in enumerate(rows, 1)]
    write_csv(os.path.join(args.out, "characters.csv"),
              ["rank", "character", "work", "medium", "total_mentions", "posts_mentioning",
               "comments_mentioning", "post_titles", "comments_on_threads_titled_with_them",
               "first_mentioned", "last_mentioned"] + [str(y) for y in years], rows)

    # works, from explicit title mentions
    wrows = [[WORKS[i][0], w_post[i] + w_comm[i], w_post[i], w_comm[i], w_title[i], w_thread[i]]
             for i in range(nw) if w_post[i] + w_comm[i]]
    wrows.sort(key=lambda r: -r[1])
    write_csv(os.path.join(args.out, "works_by_title.csv"),
              ["work", "total_mentions", "posts_mentioning", "comments_mentioning", "post_titles",
               "comments_on_threads_titled_with_them"], wrows)

    # works by type, aggregated from their characters
    agg = {}
    for r in rows:
        key = (r[2], r[3])
        a = agg.setdefault(key, {"chars": [], "total": 0})
        a["chars"].append(r[1])
        a["total"] += r[4]
    types = sorted(agg.items(), key=lambda kv: -kv[1]["total"])
    write_csv(os.path.join(args.out, "works_by_type.csv"),
              ["work", "medium", "character_mentions", "characters_tracked", "characters"],
              [[w, m, a["total"], len(a["chars"]), "; ".join(a["chars"])] for (w, m), a in types])
    medium = defaultdict(lambda: {"works": set(), "chars": 0, "total": 0})
    for r in rows:
        medium[r[3]]["works"].add(r[2])
        medium[r[3]]["chars"] += 1
        medium[r[3]]["total"] += r[4]
    mrows = sorted(([m, len(v["works"]), v["chars"], v["total"]] for m, v in medium.items()), key=lambda r: -r[3])
    write_csv(os.path.join(args.out, "mediums.csv"), ["medium", "works", "characters", "character_mentions"], mrows)

    months = sorted(set(posts_month) | set(comments_month))
    write_csv(os.path.join(args.out, "activity_by_month.csv"), ["month", "posts", "comments"],
              [[m, posts_month[m], comments_month[m]] for m in months])

    # ANALYSIS.md
    py = Counter(); cy = Counter()
    for m in months:
        py[int(m[:4])] += posts_month[m]
        cy[int(m[:4])] += comments_month[m]
    busiest = max(months, key=lambda m: posts_month[m] + comments_month[m])
    top = sorted(top_posts, reverse=True)
    L = []
    L.append(f"# r/{args.sub}: analysis results\n")
    L.append(f"Data covers **{day(ts_lo)} to {day(ts_hi)}**: **{npost:,} posts** and **{ncomm:,} comments**.\n")
    L.append(f"{len(rows)} characters from {len(agg)} works were matched at least once. "
             f"Busiest month: **{busiest}** ({posts_month[busiest]:,} posts, {comments_month[busiest]:,} comments).\n")
    L.append("## Contents\n\n1. [Activity by year](#activity-by-year)\n2. [Top characters](#top-characters)\n"
             "3. [All characters ranked](#all-characters-ranked)\n4. [Top 10 characters per year](#top-10-characters-per-year)\n"
             "5. [Works by type (novels, manga, anime...)](#works-by-type)\n6. [Works mentioned by title](#works-mentioned-by-title)\n"
             "7. [Most-discussed threads](#most-discussed-threads)\n8. [Method and caveats](#method-and-caveats)\n")

    L.append("## Activity by year\n\n| Year | Posts | Comments |\n|---|---:|---:|")
    for y in years:
        L.append(f"| {y} | {py[y]:,} | {cy[y]:,} |")
    L.append(f"| **Total** | **{npost:,}** | **{ncomm:,}** |\n")
    L.append("Monthly figures are in [activity_by_month.csv](activity_by_month.csv).\n")

    L.append("## Top characters\n\nMentions = posts (title + body) plus comments that name the character at least once.\n")
    L.append("| Rank | Character | Work | Mentions |\n|---:|---|---|---:|")
    for r in rows[:20]:
        L.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[4]:,} |")
    L.append("")

    L.append("## All characters ranked\n\nRanked from most to least mentioned.\n")
    L.append("| Rank | Character | Work | Medium | Total | Posts | Comments | First seen | Last seen | "
             + " | ".join(str(y) for y in years) + " |")
    L.append("|---:|---|---|---|---:|---:|---:|---|---|" + "---:|" * len(years))
    for r in rows:
        L.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]:,} | {r[5]:,} | {r[6]:,} | {r[9]} | {r[10]} | "
                 + " | ".join(f"{v:,}" for v in r[11:]) + " |")
    L.append("")

    L.append("## Top 10 characters per year\n")
    for k, y in enumerate(years):
        ranked = sorted(rows, key=lambda r: -r[11 + k])[:10]
        L.append(f"**{y}:** " + ", ".join(f"{r[1]} ({r[11 + k]:,})" for r in ranked if r[11 + k]) + "\n")

    L.append("## Works by type\n\nEvery work behind a tracked character, grouped by medium. "
             "Mentions = sum of that work's character mentions.\n")
    L.append("| Medium | Works | Characters | Mentions |\n|---|---:|---:|---:|")
    for m in mrows:
        L.append(f"| {m[0]} | {m[1]} | {m[2]} | {m[3]:,} |")
    L.append("")
    for m in mrows:
        L.append(f"### {m[0]}\n\n| Work | Mentions | Characters |\n|---|---:|---|")
        for (w, med), a in types:
            if med == m[0]:
                L.append(f"| {w} | {a['total']:,} | {', '.join(a['chars'])} |")
        L.append("")

    L.append("## Works mentioned by title\n\nPosts and comments that name the work itself (not just its characters).\n")
    L.append("| Rank | Work | Total | Posts | Comments |\n|---:|---|---:|---:|---:|")
    for n, r in enumerate(wrows, 1):
        L.append(f"| {n} | {r[0]} | {r[1]:,} | {r[2]:,} | {r[3]:,} |")
    L.append("")

    L.append("## Most-discussed threads\n\n| # | Date | Comments | Title |\n|---:|---|---:|---|")
    for n, (nc, title, date, link) in enumerate(top, 1):
        t = md_escape(title[:110])
        L.append(f"| {n} | {date} | {nc:,} | [{t}](https://www.reddit.com{link}) |" if link else f"| {n} | {date} | {nc:,} | {t} |")
    L.append("")

    L.append("## Method and caveats\n")
    L.append("- Source: the [Arctic Shift](https://github.com/ArthurHeitmann/arctic_shift) Reddit archive, scraped with `scraper/scrape_subreddit.py`.")
    L.append(f"- {len(CHARACTERS)} characters and {len(WORKS)} works are matched with hand-written alias lists in `analysis/analyze_mentions.py`. "
             "A post or comment counts once per character, however many times it names them.")
    L.append("- Matching is by name, so counts are approximate: ambiguous names such as *Light*, *Kira*, *Joe* or *Eren* are matched case-sensitively but can still catch unrelated words, and characters missing from the dictionary are not counted.")
    L.append("- The character-to-work mapping was written by hand; works marked *(unidentified)* could not be confirmed.")
    L.append("- Comment counts per thread come from Reddit's `num_comments` at archive time.")
    L.append(f"\n_Generated {datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d')}._\n")
    with open(os.path.join(args.out, "ANALYSIS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("done", npost, ncomm, day(ts_lo), day(ts_hi))


if __name__ == "__main__":
    main()
