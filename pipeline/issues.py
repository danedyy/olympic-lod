"""The issues log: anything the pipeline cannot settle safely is written here for manual
review, never silently guessed."""
import csv


class IssuesLog:
    HEADER = ["stage", "file", "line", "key", "issue", "action"]

    def __init__(self):
        self.rows = []

    def add(self, stage, file, line, key, issue, action):
        self.rows.append([stage, file, line, key, issue, action])

    def write(self, path):
        rows = sorted(self.rows, key=lambda r: (r[0], r[1], int(r[2] or 0), r[3], r[4]))
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(self.HEADER)
            w.writerows(rows)
        return len(rows)
