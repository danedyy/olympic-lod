"""Stage 3 — Reconcile & link to Wikidata (the 5th star), offline from the cached snapshot.

* NOC      → its own 'national Olympic committee' item, never the country's (matrix row 23):
             the hand override if there is one, else the only current NOC item whose own or
             whose country's IOC code (P984) equals ours.
* Country  → the only item with that ISO 3166-1 alpha-3 code (P298, row 27).
* The Games, medal types, disciplines → chosen by hand (rows 35, 46).
A value with no confident match gets no link (a SHACL warning) and an issues-log line.
"""
from config import table


def reconcile(clean, log):
    links, snap = table("wikidata_links"), table("wikidata_snapshot")
    overrides = {k: v for k, v in links["noc_overrides"].items() if not k.startswith("_")}

    noc = {}
    for code in sorted(clean["nocs"]):
        candidates = sorted(snap["nocs"].get(code, {}))
        q = overrides[code] if code in overrides else (candidates[0] if len(candidates) == 1 else None)
        if q:
            noc[code] = q
        else:
            log.add("reconcile", "", "", code, "no Wikidata item for this NOC"
                    + (f" (candidates: {', '.join(candidates)})" if candidates else ""), "no owl:sameAs")

    country = {}
    for iso in sorted(clean["countries"]):
        candidates = sorted(snap["countries"].get(iso, {}))
        if len(candidates) == 1:
            country[iso] = candidates[0]
        else:
            log.add("reconcile", "", "", iso, f"{len(candidates)} Wikidata items with this ISO code", "no owl:sameAs")

    discipline = {}
    for code, q in sorted(links["discipline"].items()):
        if q:
            discipline[code] = q
        else:
            log.add("reconcile", "", "", code, f"no exact Wikidata item for '{clean['disciplines'][code]}'",
                    "no skos:exactMatch")
    if set(links["discipline"]) != set(clean["disciplines"]):
        raise SystemExit("wikidata_links.json does not list exactly the disciplines of the source")

    return {"noc": noc, "country": country, "discipline": discipline,
            "medal_type": links["medal_type"], "games": links["games"], "retrieved": snap["retrieved"]}
