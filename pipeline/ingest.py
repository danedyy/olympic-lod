"""Stage 1 — Ingest: read the five Kaggle CSVs, after checking they are the expected export.

The dataset is static (Kaggle: "update frequency: never"). The SHA-256 check makes a
new or edited export fail loudly instead of being converted silently; to convert a new
release, review it and update data/source/SHA256SUMS.
"""
import csv
import hashlib
import os

from config import FILES, SOURCE


def expected_hashes():
    with open(os.path.join(SOURCE, "SHA256SUMS"), encoding="utf-8") as f:
        return {name: digest for digest, name in (line.split() for line in f if line.strip())}


def ingest():
    hashes = expected_hashes()
    data = {}
    for name in FILES:
        path = os.path.join(SOURCE, name + ".csv")
        with open(path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        if digest != hashes[name + ".csv"]:
            raise SystemExit(f"{name}.csv does not match data/source/SHA256SUMS: a new source release? Review it first.")
        with open(path, encoding="utf-8", newline="") as f:
            data[name] = list(csv.DictReader(f))
    return data
