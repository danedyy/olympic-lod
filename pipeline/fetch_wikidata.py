"""Fetch the Wikidata snapshot once (network); the pipeline itself only reads the saved file.

    python3 pipeline/fetch_wikidata.py

Writes decision_tables/wikidata_snapshot.json with the retrieval date:
  * nocs       every current 'national Olympic committee' item (Q183288, no P576 dissolved date)
               with its own IOC code and its country's IOC code (P984);
  * countries  the items whose ISO 3166-1 alpha-3 code (P298) is one of our officials' countries;
  * labels     the English label of every item chosen by hand in wikidata_links.json.
Re-running it can change the links (Wikidata is edited); commit the new snapshot on purpose.
"""
import datetime
import json
import os
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clean import clean  # noqa: E402
from config import TABLES, table  # noqa: E402
from ingest import ingest  # noqa: E402
from issues import IssuesLog  # noqa: E402

ENDPOINT = "https://query.wikidata.org/sparql"
AGENT = "olympic-lod/1.0 (https://github.com/danedyy/olympic-lod)"

NOCS = """
SELECT ?item ?label ?code WHERE {
  ?item wdt:P31 wd:Q183288 .
  FILTER NOT EXISTS { ?item wdt:P576 ?dissolved }
  { ?item wdt:P984 ?code } UNION { ?item wdt:P17/wdt:P984 ?code }
  OPTIONAL { ?item rdfs:label ?label FILTER (lang(?label) = "en") }
}"""

COUNTRIES = """
SELECT ?item ?label ?code WHERE {
  VALUES ?code { %s }
  ?item wdt:P298 ?code .
  OPTIONAL { ?item rdfs:label ?label FILTER (lang(?label) = "en") }
}"""

LABELS = """
SELECT ?item ?label WHERE {
  VALUES ?item { %s }
  ?item rdfs:label ?label FILTER (lang(?label) = "en")
}"""


def query(sparql):
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": sparql, "format": "json"})
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(request, timeout=180) as r:
        rows = json.load(r)["results"]["bindings"]
    time.sleep(1)
    return [{k: v["value"].rsplit("/", 1)[-1] if v["type"] == "uri" else v["value"] for k, v in row.items()}
            for row in rows]


def grouped(rows):
    out = {}
    for r in rows:
        out.setdefault(r["code"], {})[r["item"]] = r.get("label", "")
    return {code: dict(sorted(items.items())) for code, items in sorted(out.items())}


def main():
    isos = sorted(clean(ingest(), IssuesLog())["countries"])
    links = table("wikidata_links")
    chosen = {links["games"], *links["medal_type"].values(), *links["discipline"].values(),
              *(q for k, q in links["noc_overrides"].items() if not k.startswith("_"))} - {None}
    labels = {r["item"]: r.get("label", "") for r in query(LABELS % " ".join("wd:" + q for q in sorted(chosen)))}
    snapshot = {
        "retrieved": datetime.date.today().isoformat(),
        "endpoint": ENDPOINT,
        "nocs": grouped(query(NOCS)),
        "countries": grouped(query(COUNTRIES % " ".join(f'"{c}"' for c in isos))),
        "labels": dict(sorted(labels.items())),
    }
    missing = sorted(chosen - set(snapshot["labels"]))
    if missing:
        raise SystemExit(f"hand-chosen items not found on Wikidata: {missing}")
    path = os.path.join(TABLES, "wikidata_snapshot.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"{path}: {len(snapshot['nocs'])} IOC codes, {len(snapshot['countries'])} countries, {len(labels)} labels")


if __name__ == "__main__":
    main()
