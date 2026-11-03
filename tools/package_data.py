"""Gzip the raw .jsonl files and split them into parts under GitHub's 100 MB limit.

Usage: python tools/package_data.py [--data data] [--part-mb 90]
Creates data/<name>.jsonl.gz.part001, part002, ...  (rebuild with tools/rebuild_data.py)
"""
import argparse
import glob
import gzip
import os


class PartWriter:
    def __init__(self, prefix, part_bytes):
        self.prefix, self.part_bytes = prefix, part_bytes
        self.n, self.size, self.f = 0, 0, None

    def write(self, b):
        while b:
            if self.f is None or self.size >= self.part_bytes:
                if self.f:
                    self.f.close()
                self.n += 1
                self.f = open(f"{self.prefix}.part{self.n:03d}", "wb")
                self.size = 0
            room = self.part_bytes - self.size
            self.f.write(b[:room])
            self.size += len(b[:room])
            b = b[room:]

    def flush(self):
        pass

    def close(self):
        if self.f:
            self.f.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--part-mb", type=int, default=90)
    args = ap.parse_args()
    for src in sorted(glob.glob(os.path.join(args.data, "*.jsonl"))):
        prefix = src + ".gz"
        for old in glob.glob(prefix + ".part*"):
            os.remove(old)
        out = PartWriter(prefix, args.part_mb * 1024 * 1024)
        with open(src, "rb") as f, gzip.GzipFile(filename=os.path.basename(src), mode="wb", fileobj=out, compresslevel=9) as gz:
            while chunk := f.read(16 * 1024 * 1024):
                gz.write(chunk)
        out.close()
        print(f"{src}: {out.n} part(s)")


if __name__ == "__main__":
    main()
