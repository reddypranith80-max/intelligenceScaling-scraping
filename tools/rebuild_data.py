"""Rebuild the raw .jsonl files from the split .gz parts in data/.

Usage: python tools/rebuild_data.py [--data data]
"""
import argparse
import glob
import gzip
import io
import os
import re


class Parts(io.RawIOBase):
    """Read several files back-to-back as one stream."""

    def __init__(self, paths):
        self.paths, self.f = list(paths), None

    def readable(self):
        return True

    def readinto(self, buf):
        while True:
            if self.f is None:
                if not self.paths:
                    return 0
                self.f = open(self.paths.pop(0), "rb")
            n = self.f.readinto(buf)
            if n:
                return n
            self.f.close()
            self.f = None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    args = ap.parse_args()
    groups = {}
    for p in glob.glob(os.path.join(args.data, "*.jsonl.gz.part*")):
        groups.setdefault(re.sub(r"\.gz\.part\d+$", "", p), []).append(p)
    if not groups:
        raise SystemExit(f"no *.jsonl.gz.part* files in {args.data}")
    for dst, parts in sorted(groups.items()):
        parts.sort()
        with gzip.GzipFile(fileobj=io.BufferedReader(Parts(parts))) as gz, open(dst, "wb") as out:
            while chunk := gz.read(16 * 1024 * 1024):
                out.write(chunk)
        print(f"{dst}: rebuilt from {len(parts)} part(s)")


if __name__ == "__main__":
    main()
