"""Stage 5 — Validate the whole graph against the LDAP's SHACL shapes; fail loudly on violations.

Recommended (R) values that are missing are reported as warnings and do not fail the run
(see README, Design choices). The report is written as a sorted CSV, so that it is stable
between runs (the SHACL report graph is made of blank nodes).
"""
import csv

from pyshacl import validate as shacl_validate
from rdflib import Graph
from rdflib.namespace import SH

from config import SHAPES

HEADER = ["severity", "focus_node", "path", "value", "message"]


def validate(g):
    conforms, report, _ = shacl_validate(g, shacl_graph=Graph().parse(SHAPES), inference="none",
                                         allow_warnings=True)
    rows = sorted([str(report.value(r, SH.resultSeverity)).rsplit("#", 1)[1],
                   str(report.value(r, SH.focusNode)), str(report.value(r, SH.resultPath) or ""),
                   str(report.value(r, SH.value) or ""), str(report.value(r, SH.resultMessage))]
                  for r in report.subjects(SH.resultSeverity, None))
    return conforms, rows


def write_report(rows, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(HEADER)
        w.writerows(rows)
