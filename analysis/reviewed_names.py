"""Loads reviewed_names.txt: hand-checked labels for names found by discover_entities.py."""
import os

CHARACTERS = []   # (name, work, medium, [aliases])
WORKS = []        # (name, medium, [aliases])
EXTRA = {}        # existing character name -> [extra aliases]

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "reviewed_names.txt"), encoding="utf-8") as _f:
    for _line in _f:
        _line = _line.rstrip("\n")
        if not _line or _line.startswith("#"):
            continue
        _p = _line.split("|")
        if _p[0] == "C" and len(_p) >= 5:
            CHARACTERS.append((_p[1], _p[2], _p[3], [a.strip() for a in _p[4].split(",") if a.strip()]))
        elif _p[0] == "+" and len(_p) >= 3:
            EXTRA.setdefault(_p[1], []).extend(a.strip() for a in _p[2].split(",") if a.strip())
        elif _p[0] == "W" and len(_p) >= 4:
            WORKS.append((_p[1], _p[2], [a.strip() for a in _p[3].split(",") if a.strip()]))
