"""Tokyo 2020 → 5-star Linked Open Data: the whole pipeline.

    python3 pipeline/run.py

ingest → clean → teams → reconcile (Wikidata snapshot) → map to RDF → derive → validate → publish.
Writes data/rdf/tokyo2020.ttl, validation-report.csv and issues-log.csv. Exits with status 1,
writing no data, if the graph has any SHACL violation.
"""
import collections
import os
import sys

from clean import clean as clean_stage
from config import OUT
from derive import derive
from ingest import ingest
from issues import IssuesLog
from reconcile import reconcile
from teams import build
from to_rdf import to_rdf
from validate import validate, write_report


def main():
    log = IssuesLog()
    clean = clean_stage(ingest(), log)
    teams = build(clean, log)
    links = reconcile(clean, log)
    g = to_rdf(clean, teams, links)
    derived = derive(g)
    conforms, results = validate(g)

    os.makedirs(OUT, exist_ok=True)
    write_report(results, os.path.join(OUT, "validation-report.csv"))
    issues = log.write(os.path.join(OUT, "issues-log.csv"))
    print(f"{len(g)} triples ({derived} derived oly:coachesAthlete); {issues} issues logged")
    print(f"SHACL: {'conforms' if conforms else 'VIOLATIONS'} ({len(results)} results)")
    for (severity, message), n in sorted(collections.Counter((r[0], r[4]) for r in results).items()):
        print(f"  {severity} ×{n}: {message}")
    if not conforms:
        print("FAILED: the graph violates the profile; see data/rdf/validation-report.csv", file=sys.stderr)
        return 1
    g.serialize(os.path.join(OUT, "tokyo2020.ttl"), format="turtle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
